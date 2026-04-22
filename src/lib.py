# lib.py
import os
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, Field

# Langchain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser # <--- THÊM MỚI

# Elastic
from elasticsearch import Elasticsearch