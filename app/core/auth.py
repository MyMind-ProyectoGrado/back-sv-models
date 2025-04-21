from fastapi import Depends, HTTPException, Request
import jwt  

async def get_current_user(request: Request):
    """Extracts user ID from JWT token passed by APISIX."""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.split(" ")[1]  # Get token after "Bearer "
    
    try:
        # Extract `sub` (user ID) without validating the token
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token structure")
        return user_id
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token format")
