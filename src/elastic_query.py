# elastic_query.py
import json
from lib import BaseModel
from init import INDEX_MAPPING, COURSE_FIELD_MAP, PROGRAM_FIELD_MAP

COURSE_METADATA_FIELDS = ["ten_mon_hoc", "ma_mon_hoc", "so_tin_chi", "hoc_phan_tien_quyet"]
PROGRAM_METADATA_FIELDS = ["ten_nganh", "nien_khoa", "he_dao_tao"]

def build_hybrid_elastic_queries(intent_type: str, data: BaseModel, original_text: str, query_vector: list, top_k: int = 30):
    index_name = INDEX_MAPPING.get(intent_type)
    data_dict = data.model_dump(exclude_none=True)
    should_clauses = []
    
    # --- A. METADATA BOOSTING ---
    target_metadata_list = COURSE_METADATA_FIELDS if intent_type == "course" else PROGRAM_METADATA_FIELDS
    for field in target_metadata_list:
        if field in data_dict:
            value = data_dict[field]
            if isinstance(value, (int, float)):
                should_clauses.append({"term": {f"metadata.{field}": {"value": value, "boost": 10.0}}})
            else:
                should_clauses.append({"match": {f"metadata.{field}": {"query": str(value), "boost": 10.0, "fuzziness": "AUTO"}}})

    # --- B. DETAIL FIELDS BOOSTING ---
    field_map = COURSE_FIELD_MAP if intent_type == "course" else PROGRAM_FIELD_MAP
    for bool_key, target_field_type_value in field_map.items():
        if data_dict.get(bool_key) is True:
            should_clauses.append({"match": {"metadata.field_type": {"query": target_field_type_value, "boost": 3.0}}})

    # --- C. FULL TEXT (BM25) ---
    should_clauses.append({"match": {"text": {"query": original_text, "boost": 1.0}}})
    
    # 1. Body cho BM25 Query
    bm25_body = {
        "size": top_k,
        "query": {"bool": {"should": should_clauses, "minimum_should_match": 1}},
        "_source": ["text", "metadata"]
    }
    
    # 2. Body cho KNN Vector Query
    knn_body = {
        "size": top_k,
        "knn": {
            "field": "vector", 
            "query_vector": query_vector, 
            "k": top_k, 
            "num_candidates": 50
        },
        "_source": ["text", "metadata"]
    }
    
    return index_name, bm25_body, knn_body