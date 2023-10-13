original_index_mappings = {
    "properties": {
        "content_type": {
            "type": "text",
        },
        "text": {
            "type": "text",
        },
        "text_hash": {
            "type": "text",
        },
        "title": {
            "type": "text",
        },
        "user_id": {
            "type": "long"
        },
        "timestamp": {
            "type": "date",
            "format": "epoch_millis"
        }
    }
}

chunk_index_mappings = {
    "properties": {
        "metadata": {
            "properties": {
                "content_type": {
                    "type": "keyword"
                },
                "url": {
                    "type": "keyword"
                },
                "text_hash": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text"
                },
                "user_id": {
                    "type": "long"
                }
            }
        },
        "text": {
            "type": "text"
        },
        "vector": {
            "type": "dense_vector",
            "dims": 1536,
            "index": True,
            "similarity": "cosine"
        }
    }
}
