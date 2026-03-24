# GraphAgent Configuration

## Imports and Pre-Execution
Necessary imports
```
from neo4j import GraphDatabase
import re
from pathlib import Path
import ollama
import json
```

In order to add files it is necessary to indicate a folder inside the variable ``SOURCE_TEXT_FOLDER``.

To access neo4j it is necessary to specifiy the ``URI`` and the ``NEO4J_AUTH`` variables.

In particular an instance of neo4j should be running on port 7687. In our example the running instance is using docker.

```
sudo docker run -d --name neo4j-proto -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/testpassword neo4j:5
```
This is the running instance.

It is running on two ports because the actual web interface runs on :7474 and the bolt protocol for authentication, communication and data retrieval runs on :7687.

## Extraction and Parsing

The first function to be run is ``extract_structured_texts_from_folder``, which loads the information as ``data`` and ``source_files``.

```
data, source_files = extract_structured_texts_from_folder(SOURCE_TEXT_FOLDER)

print(f"Loaded {len(source_files)} text files from: {SOURCE_TEXT_FOLDER}")
print(f"Total extracted blocks: {len(data)}")
```
 ``extract_structured_texts_from_folder`` runs as manager function of a slave function called ``extract_structured_text`` which process the single internals of the files.

 While ``extract_structured_texts_from_folder`` runs iteratively on each file, ``extract_structured_text`` runs inside each file and splits the file in ``type:Paragraph`` and ``type:Title``, using syntactic chunking for "Title" and "Paragraph" identification.

Once the paragraphs and title are exported it is possible to use an Agent to create the relationship to connect entities. This is performed trought the use of the ``self_discovery_and_extract`` function, which semantically extract the relationships and the entities.

Then it is necessary to clean the output using ``stream_relationship`` function. In charge of cleaning the LM's output.

## Triplets Uploading 
To upload the triplets it is possible to use the ``upload_triplets`` function.

## Knowledge-base Composition
The knowledge base is composed by three main components:
- Knowledge Graph
- Title Vector Storage
- Paragraph Vector Storage

## Knowledge Retrieval 

The retrieval is performed using a 4 steps pipeline.
First a vector search is performed using the **Cosine Similarity** for Semantic Title Retrieval, then using the **neo4j** directives it performs a Graph Expansion of the linked nodes to the title paragraph using the function ``_get_paragraph_neighbors``.

Then the function ``neighbors_per_paragraph_hit`` ensures that the high-quality nodes are kept and the lower-quality are discarded.

High-quality nodes are filtered using a combination of **Paragraph Grounding Hard Constraints** and **Set-based Deduplication**. 

**Paragraph Grounding**: a specific query is run to ensure that a relationship `[r]` is present as an edge of the current expanded node.

In particular if the query: 
``` MATCH (p:Paragraph {name: $title})-[r]-(n)```
has candidates in the vector storage but it is not connected to the paragraph, then it is ignored.

The deduplication is avoided using a ``seen`` set which stores the nodes already visited.


Then it reruns a vector search for the **Neighbor Names** against the section title store to find their high-level document header. This part of the pipeline is necessary to retrieve the actual content that will be used for the context generation.

The goal is to solve **Context Fragmentation**, with having in mind that the goal isn't to find the needle, but to find the sourounding haystack of the needle, if the haystack if informative it will create a high-quality response.

## Problems
The main problem is the safe embedding mechanism. The paragraphs may be longer than the embedding model's context window, this needs to be solved using a truncation mechanism:

$next_{max} = max(min_{chars}, int(max_{chars} \cdot 0.75))$

Which means that the last part of the chunk (the one after the 0.75 percentiles) is discarde. Thought this limitation is necessary it could be solved by adding longer context windows, which could increase latency in embedding production.

