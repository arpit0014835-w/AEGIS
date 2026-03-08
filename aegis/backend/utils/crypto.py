""" 
AEGIS — Cryptography Utilities 
================================	
SHA-256 hashing and whitespace steganography for authorship watermarking.	
""" 

from __future__ import annotations 

import hashlib	
import re	
from typing import Optional 

from utils.logger import get_logger 

logger = get_logger(__name__)	


# ─── SHA-256 Hashing ────────────────────────────────────────────────────────	

def sha256_hash(data: str) -> str:	
    """Compute SHA-256 hex digest of a string.""" 
    return hashlib.sha256(data.encode("utf-8")).hexdigest() 


def sha256_file(file_path: str) -> str: 
    """Compute SHA-256 hex digest of a file's contents.""" 
    h = hashlib.sha256() 
    with open(file_path, "rb") as f:	
        for chunk in iter(lambda: f.read(8192), b""):	
            h.update(chunk) 
    return h.hexdigest() 


def generate_author_hash(author_id: str, salt: str = "") -> str:	
    """	
    Generate a deterministic author identifier hash. 

    Parameters 
    ----------	
    author_id : str	
        Author's unique identifier (email, username, etc.).	
    salt : str 
        Optional salt for additional uniqueness. 

    Returns	
    ------- 
    str	
        64-character hex digest.	
    """ 
    return sha256_hash(f"{author_id}:{salt}") 


# ─── Whitespace Steganography ───────────────────────────────────────────────	
# 
# Encodes binary data into trailing whitespace on code lines.	
# - A space (0x20) encodes a '0' bit 
# - A tab  (0x09) encodes a '1' bit	
#	
# This is invisible in most editors and preserves code semantics. 

def _string_to_bits(s: str) -> list[int]: 
    """Convert a string to a list of bits."""	
    bits: list[int] = [] 
    for byte in s.encode("utf-8"): 
        for i in range(7, -1, -1): 
            bits.append((byte >> i) & 1)	
    return bits	


def _bits_to_string(bits: list[int]) -> str: 
    """Convert a list of bits back to a string.""" 
    chars: list[int] = []	
    for i in range(0, len(bits) - 7, 8): 
        byte = 0	
        for j in range(8): 
            byte = (byte << 1) | bits[i + j] 
        chars.append(byte)	
    return bytes(chars).decode("utf-8", errors="replace")	


def embed_watermark(source_code: str, author_hash: str, bit_count: int = 64) -> str: 
    """	
    Embed an authorship watermark into source code via trailing whitespace.	

    Parameters 
    ----------
    source_code : str
        Original source code.
    author_hash : str
        SHA-256 hex digest to embed (first `bit_count` bits used).
    bit_count : int
        Number of bits to embed (default 64 = 8 hex chars).

    Returns
    -------
    str
        Watermarked source code.
    """
    # Take first bit_count bits from the hash
    hash_bits = _string_to_bits(author_hash[:bit_count // 8])[:bit_count]

    lines = source_code.split("\n")
    watermarked: list[str] = []

    bit_idx = 0
    for line in lines:
        stripped = line.rstrip()
        if bit_idx < len(hash_bits) and stripped:  # Only watermark non-empty lines
            marker = " " if hash_bits[bit_idx] == 0 else "\t"
            watermarked.append(stripped + marker)
            bit_idx += 1
        else:
            watermarked.append(stripped)

    logger.info(
        "watermark.embedded",
        bits_written=bit_idx,
        total_bits=len(hash_bits),
    )
    return "\n".join(watermarked)


def extract_watermark(source_code: str, bit_count: int = 64) -> Optional[str]:
    """
    Extract a watermark from source code trailing whitespace.

    Returns
    -------
    Optional[str]
        Extracted payload string, or None if insufficient bits found.
    """
    lines = source_code.split("\n")
    bits: list[int] = []

    for line in lines:
        if len(bits) >= bit_count:
            break
        if not line.rstrip():
            continue

        trailing = line[len(line.rstrip()):]
        if trailing:
            first_char = trailing[0]
            if first_char == " ":
                bits.append(0)
            elif first_char == "\t":
                bits.append(1)

    if len(bits) < bit_count:
        logger.warning("watermark.extract.insufficient_bits", found=len(bits))
        return None

    extracted = _bits_to_string(bits[:bit_count])
    logger.info("watermark.extracted", bit_count=len(bits))
    return extracted


def verify_watermark(
    source_code: str,
    claimed_author_id: str,
    salt: str = "",
    bit_count: int = 64,
) -> bool:
    """
    Verify that a watermark matches the claimed author.

    Parameters
    ----------
    source_code : str
        Watermarked source code.
    claimed_author_id : str
        ID claimed by the author.
    salt : str
        Salt used during watermark embedding.
    bit_count : int
        Number of bits to verify.

    Returns
    -------
    bool
        True if the watermark matches.
    """
    extracted = extract_watermark(source_code, bit_count)
    if extracted is None:
        return False

    expected_hash = generate_author_hash(claimed_author_id, salt)
    expected_payload = expected_hash[:bit_count // 8]

    return extracted == expected_payload
