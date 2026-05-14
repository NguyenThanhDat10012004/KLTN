# backend_service.py
import json

from torchgen import context
import init # Trỏ thẳng vào module init
from prompt import rephrase_chain, classifier_chain, course_chain, program_chain, answer_prompt
from elastic_query import build_hybrid_elastic_queries
from vllm import SamplingParams

ALPHA = 0.7
TOP_K_CONTEXT = 3
MAX_CONTEXT_TOKENS = 1500

def min_max_normalize(scores_dict):
    if not scores_dict: return {}
    scores = list(scores_dict.values())
    min_s, max_s = min(scores), max(scores)
    return {k: (v - min_s) / (max_s - min_s) if max_s != min_s else 1.0 for k, v in scores_dict.items()}

def ensemble_fusion(bm25_norm, vec_norm, alpha):
    all_ids = set(bm25_norm.keys()).union(set(vec_norm.keys()))
    combined = {doc_id: alpha * vec_norm.get(doc_id, 0.0) + (1 - alpha) * bm25_norm.get(doc_id, 0.0) for doc_id in all_ids}
    return sorted(combined.keys(), key=lambda x: combined[x], reverse=True)

def get_answer_from_llm(user_query: str, chat_history: list, user_context: dict = None):
    user_info_str = ", ".join([f"{k}: {v}" for k, v in user_context.items() if v]) if user_context else "Không có thông tin cụ thể"
    print(f"\n=== Nhận được câu hỏi: '{user_query}' với ngữ cảnh người dùng: {user_info_str} ===")
    history_text = "\n".join([f"{'User' if m['role']=='user' else 'AI'}: {m['content']}" for m in chat_history[-10:]]) if chat_history else "Không có lịch sử."

    try:
        print(f"\n🔄 [1] RAW QUERY: '{user_query}'")
        processing_query = rephrase_chain.invoke({"chat_history": history_text, "query": user_query, "user_info": user_info_str})
        print(f"🔄 [1] REPHRASED QUERY: '{processing_query}'")
        intent_res = classifier_chain.invoke({"query": processing_query, "user_info": user_info_str})
        intent = intent_res.intent_type.lower()
        print(f"🔍 [2] INTENT: {intent.upper()}")
        
        extracted_data = None
        if intent == "course":
            extracted_data = course_chain.invoke({"query": processing_query, "user_info": user_info_str})
        elif intent == "program":
            extracted_data = program_chain.invoke({"query": processing_query, "user_info": user_info_str})

        context_text = "Không tìm thấy dữ liệu liên quan."
        if intent != "unknown" and extracted_data:
            print("🔄 [3.1] Embedding query...")
            # GỌI MODEL QUA INIT MODULE
            query_vector = init.embed_model.encode([processing_query])[0].tolist()
            
            index_name, bm25_body, knn_body = build_hybrid_elastic_queries(intent, extracted_data, processing_query, query_vector)
            
            search_requests = [{"index": index_name}, bm25_body, {"index": index_name}, knn_body]
            msearch_resp = init.es_client.msearch(body=search_requests)
            bm25_resp, vec_resp = msearch_resp['responses'][0], msearch_resp['responses'][1]

            bm25_scores, vec_scores, doc_store = {}, {}, {}
            for h in bm25_resp.get("hits", {}).get("hits", []):
                print(f"BM25 Hit: ID={h['_id']}, Score={h['_score']}")
                bm25_scores[h["_id"]] = h["_score"]
                doc_store[h["_id"]] = h["_source"].get("text", "")
            for h in vec_resp.get("hits", {}).get("hits", []):
                print(f"Vector Hit: ID={h['_id']}, Score={h['_score']}")
                vec_scores[h["_id"]] = h["_score"]
                doc_store[h["_id"]] = h["_source"].get("text", "")

            fused_ids = ensemble_fusion(min_max_normalize(bm25_scores), min_max_normalize(vec_scores), ALPHA)[:30]

            print("🔄 [3.2] Reranking...")
            if fused_ids:
                pairs = [[processing_query, doc_store[doc_id]] for doc_id in fused_ids]
                rerank_scores = init.reranker.compute_score(pairs)
                reranked_docs = sorted(zip(fused_ids, rerank_scores), key=lambda x: x[1], reverse=True)
                reranked_ids = [doc[0] for doc in reranked_docs]
                
                current_ctxs, current_tokens = [], 0
                for doc_id in reranked_ids[:TOP_K_CONTEXT]:
                    ctx = doc_store[doc_id]
                    ctx_len = len(init.tokenizer.encode(ctx))
                    if current_tokens + ctx_len < MAX_CONTEXT_TOKENS:
                        current_ctxs.append(ctx)
                        current_tokens += ctx_len
                
                context_text = "\n\n".join([f"Đoạn {j+1}: {c}" for j, c in enumerate(current_ctxs)])
                print(f"✅ Đã chuẩn bị xong {len(current_ctxs)} đoạn Context.")

        print("🔄 [4] Sinh câu trả lời qua Llama...")
        system_content = f"""Bạn là Trợ lý ảo tư vấn học vụ UET - Trường đại học Công Nghệ.
                    Thông tin sinh viên đang hỏi: {user_info_str}

                    Nhiệm vụ: Trả lời câu hỏi dựa trên CONTEXT được cung cấp.
                    ### CONTEXT:
                    {context_text}
                    ### YÊU CẦU:
                    1. Trả lời chính xác dựa trên Context.
                    2. Nếu Context rỗng, hãy nói "Hiện chưa có dữ liệu chi tiết".
                    3. Tùy chỉnh xưng hô phù hợp với sinh viên (ví dụ: "Với sinh viên khóa {user_info_str}...")."""

# 2. Khởi tạo nội dung cho User (Ngữ cảnh & Câu hỏi)
        user_content = f"""
        ### CÂU HỎI CỦA SINH VIÊN:
        {processing_query}"""

        # 3. Đưa vào list messages chuẩn cho Llama-3.1
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        print(f"🔄 [4.1] PROMPT CHO LLM:\nSystem: {system_content}\nUser: {user_content}")
        prompt = init.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        sampling_params = SamplingParams(temperature=0.1, top_p=0.9, max_tokens=1024, stop_token_ids=[init.tokenizer.eos_token_id, init.tokenizer.convert_tokens_to_ids("<|eot_id|>")])
        
        outputs = init.llm_engine.generate([prompt], sampling_params, use_tqdm=False)
        final_answer = outputs[0].outputs[0].text.strip()
        
        return {"answer": final_answer}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"answer": f"Lỗi hệ thống: {str(e)}"}