meta:
  id: saf
  application: Feeding Frenzy
  endian: le
seq:
  - id: magic
    contents: ["FFAS"]
  - id: version
    type: u4
  - id: offset_toc
    type: u4
  
instances:
  toc:
    pos: offset_toc
    type: toc
    size-eos: true
    
types:
  toc:
    seq:
      - id: toc_header 
        type: toc_header
      - id: entries
        type: toc_entry
        # repeat: eos
        repeat: expr
        repeat-expr: toc_header.entry_count
  
  toc_header:
    seq:
      - id: version
        type: u4
      - id: global_checksum
        size: 0x10
      - id: entry_count
        type: u4
        
  toc_entry:
    seq:
      - id: data_start
        type: u4
      - id: data_size
        type: u4
      - id: checksum
        size: 0x10
      - id: path_len
        type: u2
      - id: path 
        size: path_len
        type: str
        encoding: ASCII
        terminator: 0
    instances:
      file_content:
          pos: data_start
          size: data_size
          io: _root._io