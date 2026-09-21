"""
AVDS (Authenticated Verifiable Data Structure) — 独立子系统

本模块实现基于 q=2 树结构的可验证数据结构，依赖 clvc_aux.py 中的 CLVC 向量承诺。

注意：这不是当前 OVDS 主流程的一部分。OVDS 的密码层实现见 src/vads_lib.py（VADS 协议）。
请勿在同一数据流中将本模块与 vads_lib 混用。

协议完整流程说明：OVDS协议完整流程.md（第十三节）
"""
