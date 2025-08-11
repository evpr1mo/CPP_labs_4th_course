#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <cmath>
#include <algorithm>
#include "build/schema.pb.h"
#include <map>
#include <vector>

#include "crc32.h"

#define POOL_FLAG_IS_FREE 0x0001
#define POOL_FLAG_IS_INTERESTING 0x0004
#define POOL_FLAG_IS_FOR_CHUNK 0x0008
// ??

struct Pool_Node {
    Pool_Node *prev;
    Pool_Node *next;
    size_t data_size;
    int64_t flags;
    // then data
};

struct Interesting_Pool_Node {
    int64_t hint_key;
    int64_t hint_length;
};

struct SubHeader {
    uint64_t key;
    uint64_t data_length;
};

struct PayloadChunkHeader {
    size_t index;  // index of a chunk (number)
    uint64_t key;  // Encryption key for some other chunk (see below)!
    uint64_t crc32;  // Hash of a decrypted chunk
    size_t chunk_size;  // Size of a chunk in bytes.
};

// Map to hold chunk indices and their associated key ID

std::map<size_t, size_t> chunk_key_map = {
    {20, 0}, {2, 1}, {10, 2}, {31, 3}, {30, 4}, {27, 5}, {7, 6},
    {22, 7}, {18, 8}, {17, 9}, {8, 10}, {21, 11}, {26, 12}, {9, 13},
    {15, 14}, {13, 15}, {4, 16}, {14, 17}, {5, 18}, {3, 19}, {11, 20},
    {29, 21}, {12, 22}, {23, 23}, {25, 24}, {16, 25}, {1, 26}, {0, 27},
    {19, 28}, {28, 29}, {6, 30}, {24, 31}
};


size_t read_file(const char *fname, void **dst)
{
    FILE *f = fopen(fname, "rb");
    if (NULL == f) {
        fprintf(stderr, "File not found: %s\n", fname);
        exit(1);
    }
    fseek(f, 0L, SEEK_END);
    size_t sz = ftell(f);
    fseek(f, 0L, SEEK_SET);
    *dst = malloc(sz);
    sz = fread(*dst, 1, sz+1, f);
    assert(feof(f));
    fclose(f);
    return sz;
}

// ----------------------------------------------
    // Implement XOR encoding/decoding.
    // This is very simple.
    // Key is uint64 - 8 bytes.
    // Each 8 bytes of `data` must be XOR'ed with the Key.
    //
    // Please note! `data_size` may be not divisible by 8.
    // In that case, cast the key to uint8_t XOR all the
    // remaining bytes with it.
    // ----------------------------------------------
    // A good test for `xor_encdec_8` is to apply it twice
    // Since, well, as you know, a xor k xor k = a

void xor_encdec_8(void *data, size_t data_size, uint64_t key)
{
   uint8_t *byte_data = (uint8_t *)data;
    size_t i = 0;

    while (i + 8 <= data_size) {
        *(uint64_t *)(byte_data + i) ^= key;
        i += 8;
    }

    uint8_t key_byte = (uint8_t)(key & 0xFF);
    while (i < data_size) {
        byte_data[i] ^= key_byte;
        ++i;
    }
}

//(added) function Processing marked nodes
void process_interesting_nodes(Pool_Node *head) {
    Pool_Node *node = head;
    while (node) {
        if (node->flags & POOL_FLAG_IS_INTERESTING) {
            uint8_t *payload = (uint8_t *)(node + 1);
            Interesting_Pool_Node *interesting = (Interesting_Pool_Node *)payload;

            uint64_t hint_key = interesting->hint_key;
            size_t hint_length = interesting->hint_length;
            uint8_t *hint_data = payload + sizeof(Interesting_Pool_Node);

            // Decrypt the hint
            xor_encdec_8(hint_data, hint_length, hint_key);

            printf("Decrypted hint: %.*s\n", (int)hint_length, hint_data);

            // Parse the SubHeader
            SubHeader *subheader = (SubHeader *)(hint_data + hint_length);
            printf("SubHeader: key = %lu, data_length = %lu\n", subheader->key, subheader->data_length);

            // Decrypt the data using the key from SubHeader
            uint8_t *data = (uint8_t *)(subheader + 1);
            xor_encdec_8(data, subheader->data_length, subheader->key);

            // Save or process the decrypted data
            // For now, print a part of the data (as ASCII) and save it if it’s schema
            if (strstr((char *)hint_data, "protobuf schema file")) {
                FILE *schema_file = fopen("schema.proto", "w");
                fwrite(data, 1, subheader->data_length, schema_file);
                fclose(schema_file);
                printf("Saved Protobuf schema to 'schema.proto'\n");
            } else if (strstr((char *)hint_data, "protobuf message")) {
                FILE *message_file = fopen("message.bin", "wb");
                fwrite(data, 1, subheader->data_length, message_file);
                fclose(message_file);
                printf("Saved Protobuf message to 'message.bin'\n");
            }
        }
        node = node->next;
    }
}


void decode_protobuf_message(const char *filename) {
    // Open the Protobuf message file
    FILE *file = fopen(filename, "rb");
    if (!file) {
        fprintf(stderr, "Failed to open file: %s\n", filename);
        return;
    }

    // Read the file into a buffer
    fseek(file, 0, SEEK_END);
    size_t file_size = ftell(file);
    fseek(file, 0, SEEK_SET);

    uint8_t *buffer = (uint8_t *)malloc(file_size);
    fread(buffer, 1, file_size, file);
    fclose(file);

    // Parse the message using Protobuf
    NextHint hint;
    if (hint.ParseFromArray(buffer, file_size)) {
        printf("Decoded Protobuf message:\n");
        printf("Hint Message: %s\n", hint.hint_message().c_str());

        for (int i = 0; i < hint.chunks_info_size(); ++i) {
            const PayloadChunk &chunk = hint.chunks_info(i);
            printf("Chunk ID: %ld, Key ID: %ld\n", chunk.chunk_id(), chunk.key_id());
        }
    } else {
        fprintf(stderr, "Failed to parse Protobuf message.\n");
    }

    free(buffer);
}


void process_chunks(Pool_Node *head) {
    std::vector<PayloadChunkHeader *> chunks(32);

    Pool_Node *node = head;
    size_t node_count = 0;

    while (node) {
        std::cout << "Processing node " << node_count << ", Flags: " << node->flags << std::endl;

        if (node->flags & POOL_FLAG_IS_FOR_CHUNK) {
            std::cout << "Node " << node_count << " is a chunk node." << std::endl;

            // Calculate payload offset safely
            uint8_t *node_memory = reinterpret_cast<uint8_t *>(node);
            size_t node_size = sizeof(Pool_Node);
            uint8_t *payload = node_memory + node_size;

            // Ensure alignment for PayloadChunkHeader
            if (reinterpret_cast<std::uintptr_t>(payload) % alignof(PayloadChunkHeader) != 0) {
                std::cerr << "Memory alignment error in node " << node_count << std::endl;
                break;
            }

            // Cast to PayloadChunkHeader
            PayloadChunkHeader *chunk_header = (PayloadChunkHeader *)payload;

            // Validate chunk header
            if (chunk_header->chunk_size == 0 || chunk_header->index >= 32) {
                std::cerr << "Invalid chunk header detected in node " << node_count << std::endl;
                break;
            }

            chunks[chunk_header->index]=chunk_header;
            std::cout << "Chunk " << chunk_header->index << " loaded." << std::endl;
        }

        node = node->next;
        node_count++;
    }

    std::cout << "Total nodes processed: " << node_count << std::endl;
    std::cout << "Total chunks found: " << chunks.size() << std::endl;

    if (chunks.empty()) {
        std::cerr << "No chunks to process. Exiting." << std::endl;
        return;
    }

    FILE *file = fopen("my_binary", "wb");



    // Process chunks (same as before)
    for (size_t i_chunk = 0; i_chunk < chunks.size(); i_chunk++) {
        try {
            std::cout << "Processing chunk " << i_chunk << std::endl;

            PayloadChunkHeader *chunk_header = chunks[i_chunk];
            std:: cout<< i_chunk<<" "<<chunk_header <<"\n";
            size_t key_id = chunk_key_map.at(chunk_header->index); // Ensure index is valid
            uint64_t encryption_key = chunks[key_id]->key;

            uint8_t *chunk_data = reinterpret_cast<uint8_t *>(chunk_header + 1);
            xor_encdec_8(chunk_data, chunk_header->chunk_size, encryption_key);

            uint32_t computed_crc32 = crc32(chunk_data, chunk_header->chunk_size);

            if (computed_crc32 != chunk_header->crc32) {
                std::cerr << "CRC mismatch for chunk " << chunk_header->index
                          << ": expected " << chunk_header->crc32
                          << ", computed " << computed_crc32 << std::endl;
            } else {
                std::cout << "Chunk " << chunk_header->index << " decrypted successfully!" << std::endl;
                fwrite(chunk_data, chunk_header->chunk_size,1,file);
            }
        } catch (const std::exception &e) {
            std::cerr << "Error processing chunk " << i_chunk << ": " << e.what() << std::endl;
        }
    }
    fclose(file);
}



/// Call this function to load the heap file.
size_t mysterious_heap_load(uint8_t **memory, const char *fname)
{
    size_t memory_size = read_file(fname, (void **)memory);
    printf("Computing heap hash.\n");
    uint32_t hash = crc32(*memory, memory_size);
    printf("crc32 = %u\n", hash);

    uint8_t *mem = *memory;
    Pool_Node *p = (Pool_Node *)(mem);
    while (NULL != p) {
        if (p->next) {
            p->next = (Pool_Node *)((uint8_t *)p->next + (uintptr_t)(*memory - 1));
        }
        if (p->prev) {
            p->prev = (Pool_Node *)((uint8_t *)p->prev + (uintptr_t)(*memory - 1));
        }
        p = p->next;
    }
    return memory_size;
}



int main()
{
    // Set path to heap file here!!
    const char *fname = "../mysterious_heap";
    uint8_t *memory = NULL;
    size_t memory_size = mysterious_heap_load(&memory, fname);

 // Cast memory to the head of the linked list
    Pool_Node *head = (Pool_Node *)memory;

    // Process interesting nodes
    //process_interesting_nodes(head);

    // Decode Protobuf message
    //decode_protobuf_message("message.bin");

    // Process chunks (decryption)
    process_chunks(head);

    // Free memory after use
    free(memory);

    return 0;
}