import sys
import os

sys.path.insert(0, "/Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS/_libs")
try:
    from striprtf.striprtf import rtf_to_text
except ImportError:
    print("striprtf not found")
    sys.exit(1)

sample = r"""{\rtf1\ansi\ansicpg1252\cocoartf2761
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset0 HelveticaNeue;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx220\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0
{\listtext1.}\f0\fs24 \cf0 First item\
{\listtext2.}Second item\
{\listtext\uc0\u8259 }Bullet item}
"""
print(repr(rtf_to_text(sample)))
