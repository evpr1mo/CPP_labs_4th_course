# Task 1

In this task, I give you a mysterious binary file. You have to figure out a way to extract
an important data from it and save it to the disk.

On your journey you will encounter hints on
how to proceed, but first, let me give you the
first fundamental information regarding the file.

The general structure of this file is a heap, a pool with intrusive list to be precise. The file starts with a header:

```
Pool_Node (header):
Pool_Node *prev;  // pointer to a previous node, may be NULL at the first node.
Pool_Node *next;  // pointer to a next node, may be NULL at the last node.
size_t data_size;  // size of the node's payload
int64_t flags;  // some bit flags describing the info about the node
-----
bytes of data [data_size]
```

The struct representing this header is already implemented in `mysterious_heap.cpp` - a file, which you have to finish.

The first hint is as follows:

```
Look for the nodes with POOL_FLAG_IS_INTERESTING bit set in the flag.

each interesting node's payload starts with a header

struct Interesting_Pool_Node {
    int64_t hint_key;
    int64_t hint_length;
};

after which goes the hint and the rest of the payload in the node.
```

How do you read this hint? Well, its bytes start right after the Interesting_Pool_Node header and take hint_length bytes. However, it's encrypted with a key hint_key. Use xor_encdec8 function to decrypt it.

We also use crc32 hashes in this work, mostly for debugging. The example of usage is already in the main function. By the way, make sure the printed hash of the mysterious_heap file is 2159869300.

# Below are hints, extracted in the process :) 
      |
      |
      V
      
First hints:
Computing heap hash.
crc32 = 2159869300
Decrypted hint: This is a hint. After the end of this string lays a SubHeader:
struct SubHeader {
   uint64_t key;
   uint64_t data_length;
};
This header contains an encryption key and the length of the data in bytes
that goes after this header.
In particular, this node contains the protobuf message.
You have to have a schema text to decode this message,
If you haven't located it yet, look for other interesting nodes.

Decrypted hint: This is a hint. After the end of this string lays a SubHeader:
struct SubHeader {
   uint64_t key;
   uint64_t data_length;
};
This header contains an encryption key and the length of the data in bytes
that goes after this header.
In particular, this node contains text for the protobuf schema file.
Decrypt it, print it to file, compile it with protoc, and look for another
interesting node which contains the protobuf message.


ev_primo@DESKTOP-0HH0TOJ:/mnt/e/PyCharm/assignment2_v5_Priymak_KA13/task1/build$ cmake .. 
-- Configuring done (0.2s)
-- Generating done (0.1s)
-- Build files have been written to: /mnt/e/PyCharm/assignment2_v5_Priymak_KA13/task1/build
ev_primo@DESKTOP-0HH0TOJ:/mnt/e/PyCharm/assignment2_v5_Priymak_KA13/task1/build$ make
[ 33%] Building CXX object CMakeFiles/decode_heap.dir/mysterious_heap.cpp.o
[ 66%] Building CXX object CMakeFiles/decode_heap.dir/schema.pb.cc.o
[100%] Linking CXX executable decode_heap
[100%] Built target decode_heap
ev_primo@DESKTOP-0HH0TOJ:/mnt/e/PyCharm/assignment2_v5_Priymak_KA13/task1/build$ ./decode_heap



Computing heap hash.
crc32 = 2159869300
Decoded Protobuf message:
Hint Message: Congratulations you've completed 1/2 of the task!

Next, you need to recover an important data and save
it into a file.

To do this, first, you need to locate the chunks of
this data on the heap.

The chunks are stored in nodes of the Pool with the flag's
0x0008 bit enabled.

Each chunk has a header:
struct PayloadChunkHeader {
    size_t index;  // index of a chunk (number)
    uint64_t key;  // Encryption key for some other chunk (see below)!
    uint64_t crc32;  // Hash of a decrypted chunk
    size_t chunk_size;  // Size of a chunk in bytes.
};

Note that the encryption key in a node corresponds to a node
with a different index. The mapping of (index -> index for key)
is contained in the chunks_info message in this protobuf.

For instance, for this case:
```
  o--------o   o---o           o---o
  |        |   |   |           |   |
key1       |   | key2          | key3
CHUNK1     |   | CHUNK2        | CHUNK3
  ^------- | --o   ^-----------o   ^
           o-----------------------o
```
In this example, key1 encrypts CHUNK3, key2 encrypts CHUNK1,
and key3 encrypts CHUNK2.
chunks info would be:
chunk_id = 1, key_id = 3
chunk_id = 2, key_id = 1
chunk_id = 3, key_id = 2
i.e. key_id says which chunk it encrypts.

Your task is to find all the chunks, decrypt them,
and copy them in order defined by index.
To be sure you are doing everything right, check the
crc32 hashes for each decrypted chunk.
After all chunks are put together, compute the total
hash sum (crc32), write the file memory to disk (fwrite) and
run:
```
python finalize_the_file.py --hash <hash crc32> --filepath <path_to_file>
```
e.g.
```
python finalize_the_file.py --hash 11338217 --filepath ./my_saved_binary_file
```

Chunk ID: 0, Key ID: 20
Chunk ID: 1, Key ID: 2
Chunk ID: 2, Key ID: 10
Chunk ID: 3, Key ID: 31
Chunk ID: 4, Key ID: 30
Chunk ID: 5, Key ID: 27
Chunk ID: 6, Key ID: 7
Chunk ID: 7, Key ID: 22
Chunk ID: 8, Key ID: 18
Chunk ID: 9, Key ID: 17
Chunk ID: 10, Key ID: 8
Chunk ID: 11, Key ID: 21
Chunk ID: 12, Key ID: 26
Chunk ID: 13, Key ID: 9
Chunk ID: 14, Key ID: 15
Chunk ID: 15, Key ID: 13
Chunk ID: 16, Key ID: 4
Chunk ID: 17, Key ID: 14
Chunk ID: 18, Key ID: 5
Chunk ID: 19, Key ID: 3
Chunk ID: 20, Key ID: 11
Chunk ID: 21, Key ID: 29
Chunk ID: 22, Key ID: 12
Chunk ID: 23, Key ID: 23
Chunk ID: 24, Key ID: 25
Chunk ID: 25, Key ID: 16
Chunk ID: 26, Key ID: 1
Chunk ID: 27, Key ID: 0
Chunk ID: 28, Key ID: 19
Chunk ID: 29, Key ID: 28
Chunk ID: 30, Key ID: 6
Chunk ID: 31, Key ID: 24
