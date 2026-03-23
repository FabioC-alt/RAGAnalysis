from neo4j import GraphDatabase
import re
from pathlib import Path

# Folder-based source used by extract_structured_texts_from_folder
SOURCE_TEXT_FOLDER = "dataOran/3gpp-specifications-md"

# Single Neo4j instance used only for KG relationships (triplets)
URI = "neo4j://localhost:7687"
NEO4J_AUTH = ("neo4j", "testpassword")

# Two separate vector storages for title retrieval
PARAGRAPH_VECTOR_STORE_PATH = "paragraph_title_vectors.json"
SECTION_VECTOR_STORE_PATH = "section_title_vectors.json"
EMBEDDING_MODEL = "mxbai-embed-large"

def extract_structured_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Split the text into blocks separated by at least one empty line
        raw_blocks = content.split('\n\n')

        structured_data = []

        for block in raw_blocks:
            # Clean the block and split into internal lines
            lines = [line.strip() for line in block.split('\n') if line.strip()]

            if not lines:
                continue

            if len(lines) == 1:
                structured_data.append({
                    "type": "Title",
                    "text": lines[0],
                })
            else:
                structured_data.append({
                    "type": "Paragraph",
                    "text": " ".join(lines),
                })

        return structured_data

    except FileNotFoundError:
        print(f"Error: File not found -> {file_path}")
        return []

def extract_structured_texts_from_folder(folder_path):
    folder = Path(folder_path)
    txt_files = sorted(folder.rglob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in folder: {folder_path}")
        return [], []

    combined_data = []
    for txt_file in txt_files:
        file_data = extract_structured_text(txt_file)
        for item in file_data:
            item["source_file"] = txt_file.name
        combined_data.extend(file_data)

    return combined_data, txt_files

# Execution (folder mode)
data, source_files = extract_structured_texts_from_folder(SOURCE_TEXT_FOLDER)

print(f"Loaded {len(source_files)} text files from: {SOURCE_TEXT_FOLDER}")
print(f"Total extracted blocks: {len(data)}")

# Displaying sample results
for item in data[:20]:
    print(f"[{item['type'].upper()}] ({item.get('source_file', 'N/A')}): {item['text'][:70]}...")


import re

def stream_relationships(large_text):
    # This pattern specifically targets the Relationship Format:
    # It looks for: #Number [Subject] -> [Verb] -> [Object]
    # We use \s* to handle any inconsistent spacing around the arrows.
    rel_pattern = re.compile(r"#(\d+)\s+(.*?)\s*->\s*(.*?)\s*->\s*(.*)")

    # Splitting by newline to simulate line-by-line reading
    for line in large_text.splitlines():
        clean_line = line.strip()
        
        # We only care about lines that match our specific relationship pattern
        match = rel_pattern.search(clean_line)
        if match:
            yield {
                "id": int(match.group(1)),
                "subject": match.group(2).strip(),
                "verb": match.group(3).replace(" ",""),
                "object": match.group(4).strip()
            }

import ollama
import json

def self_discover_and_extract(title, paragraphs, entity_types, predicates):
    sample_text = f"Title: {title}\n\n" + "\n".join(paragraphs[:3])

    discovery_prompt = f"""Perform Named Entity Recognition (NER) and extract knowledge graph triplets from the text. NER identifies named entities of given entity types, and triple extraction identifies relationships between entities using specified predicates.

        **Entity Types:**
        {json.dumps(entity_types)}

        **Predicates:**
        {json.dumps(predicates)}

        **Text:**
        {sample_text}

        **Example Output:**
            "entities": [{{ "text": "Google", "type": "ORGANIZATION" }}],
            "triplets": [{{ "subject": "Google", "predicate": "founded_in", "object": "USA" }}]
        """

    discovery_prompt=f""" 
                        Prompt for extracting entities: Extract key entities from the given
                        text. Extracted entities are nouns, verbs, or adjectives,
                        particularly regarding sentiment. This is for an extraction
                        task, please be thorough and accurate to the reference text.

                        Prompt for extracting relations: Extract subject-predicate-object
                        triples from the assistant message. A predicate (1-3
                        words) defines the relationship between the subject and
                        object. Relationship may be fact or sentiment based on
                        assistant’s message. Subject and object are entities.
                        Entities provided are from the assistant message and
                        prior conversation history, though you may not need all of
                        them. This is for an extraction task, please be thorough,
                        accurate, and faithful to the reference text

                        In the end represent all the relationships with this format, do not add text:
                        
                        *Relationship Format:*

                        #[Number] Entity -> Predicate -> Entity

                        {sample_text}
                        """

    # Remove the redundant .format() call — the f-string already handled substitution
    discovery_response = ollama.chat(model='llama3:8b', messages=[
        {'role': 'user', 'content': discovery_prompt}
    ])
    return discovery_response['message']['content']

# Usage
# schema, triplets = self_discover_and_extract(my_title, my_paragraphs)for p in range(len(data)-1):

for p in range(len(data)-1):
    current_val =data[p]
    next_val = data[p+1]

    if current_val['type'] == 'Title' and next_val['type'] == 'Paragraph':
        my_title = current_val['text']
        my_paragraphs = [next_val['text']]

        

        entity_types = ["Person", "Organization", "Object", "Subject"]
        predicates = ["related_to", "located_in", "participated_in"]

        data_n = self_discover_and_extract(my_title, my_paragraphs, entity_types, predicates)
        extracted_triplets = list(stream_relationships(data_n))
        # 3. Print the actual parsed dictionaries
        print(f"--- Results for: {my_title} ---")
        for triplet in extracted_triplets:
            print(triplet)

def upload_triplets(driver, triplets, paragraph_name):
    with driver.session() as session:
        for triplet in triplets:
            rel_type = re.sub(r'[^a-zA-Z0-9_]', '', triplet['verb'].replace(" ", "_").upper())
            if not rel_type:
                rel_type = "RELATED_TO"

            # Keep relation and add paragraph context links for both entities.
            query = (
                f"MERGE (s:Entity {{name: $sub}}) "
                f"MERGE (o:Entity {{name: $obj}}) "
                f"MERGE (p:Paragraph {{name: $paragraph_name}}) "
                f"MERGE (s)-[:{rel_type}]->(o) "
                f"MERGE (s)-[:MENTIONED_IN]->(p) "
                f"MERGE (o)-[:MENTIONED_IN]->(p)"
            )
            session.run(
                query,
                sub=triplet['subject'],
                obj=triplet['object'],
                paragraph_name=paragraph_name,
            )

def upload_triplets_APOC(driver, triplets, paragraph_name):
    with driver.session() as session:
        for triplet in triplets:
            # Clean the verb to make it a valid Neo4j Relationship Type
            rel_type = re.sub(r'[^a-zA-Z0-9_]', '', triplet['verb'].replace(" ", "_").upper())
            if not rel_type:
                rel_type = "RELATED_TO"

            query = """
            MERGE (s:Entity {name: $sub})
            MERGE (o:Entity {name: $obj})
            MERGE (p:Paragraph {name: $paragraph_name})
            WITH s, o, p
            CALL apoc.create.relationship(s, $rel, {}, o) YIELD rel
            MERGE (s)-[:MENTIONED_IN]->(p)
            MERGE (o)-[:MENTIONED_IN]->(p)
            RETURN rel
            """
            session.run(
                query,
                sub=triplet['subject'],
                obj=triplet['object'],
                paragraph_name=paragraph_name,
                rel=rel_type,
            )
# Integration with Ollama loop + paragraph-context links
with GraphDatabase.driver(URI, auth=NEO4J_AUTH) as driver:
    driver.verify_connectivity()

    for p in range(len(data) - 1):
        current_val = data[p]
        next_val = data[p + 1]

        if current_val['type'] == 'Title' and next_val['type'] == 'Paragraph':
            my_title = current_val['text']
            my_paragraphs = [next_val['text']]

            entity_types = ["Person", "Organization", "Object", "Subject"]
            predicates = ["related_to", "located_in", "participated_in"]

            data_n = self_discover_and_extract(my_title, my_paragraphs, entity_types, predicates)
            triplets = list(stream_relationships(data_n))

            if triplets:
                upload_triplets(driver, triplets, my_title)
                print(f"Uploaded {len(triplets)} relationships for paragraph '{my_title}'.")
            else:
                print(f"No relationships parsed for paragraph '{my_title}'; skipping Neo4j upload.")
