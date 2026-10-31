from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import ast
from typing import List
from ..security.rbac import require_role

router = APIRouter(prefix="/enterprise/ast", tags=["AST Verification"])

# Whitelisted node types – only safe constructs allowed
WHITELIST = {
    ast.Module,
    ast.Expr,
    ast.Assign,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Call,
    ast.Attribute,
    ast.List,
    ast.Tuple,
    ast.Dict,
}

class ASTVerifyRequest(BaseModel):
    code: str

class ASTVerifyResponse(BaseModel):
    safe: bool
    message: str
    disallowed_nodes: List[str] = []

def is_ast_safe(tree: ast.AST) -> (bool, List[str]):
    disallowed = []
    for node in ast.walk(tree):
        if type(node) not in WHITELIST:
            disallowed.append(type(node).__name__)
    return (len(disallowed) == 0, disallowed)

@router.post("/verify", response_model=ASTVerifyResponse)
async def verify_ast(request: ASTVerifyRequest, role: str = Depends(require_role("developer")):
    try:
        tree = ast.parse(request.code)
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Syntax error: {e}")
    safe, disallowed = is_ast_safe(tree)
    message = "AST is safe" if safe else "Unsafe AST nodes detected"
    return ASTVerifyResponse(safe=safe, message=message, disallowed_nodes=disallowed)

