original_index_mappings = {
    "properties": {
        "title": {
            "type": "text"
        },
        "text": {
            "type": "text",
        },
        "text_hash": {
            "type": "keyword"
        },
        "content_type": {
            "type": "keyword"
        },
        "url": {
            "type": "keyword"
        },
        "user_id": {
            "type": "long"
        },
        "created_at": {
            "type": "date",
            "format": "epoch_millis"
        },
        "updated_at": {
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
