#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pngs2apng is python library/executable used for converting multiple pngs
# into single apng file. It uses only standard python library.
# Copyright (C) 2016  Pavel Holica, Jiří Kortus
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import sys
import struct
import zlib

PNG_HEADER = "".join([chr(x) for x in (137, 80, 78, 71, 13, 10, 26, 10)])
PNG_HEADER_SIZE = 8
PNG_IHDR_SIZE = 25 # including length and CRC
PNG_IEND = "".join([chr(x) for x in (73, 69, 78, 68)])
PNG_IEND_SIZE = 4

def seek_IDAT(fo):
    while True:
        (size, ) = struct.unpack("!I", fo.read(4))
        frame_type = fo.read(4)
        if frame_type == "IDAT":
            return size
        if frame_type == "IEND":
            return 0
        fo.seek(size+4, 1)

def pngs2apng(target, *inpaths):
    outfile = open(target, 'w')
    # write PNG HEADER
    outfile.write(PNG_HEADER)
    # copy PNG IHDR from first file
    with open(inpaths[0]) as first:
        first.seek(PNG_HEADER_SIZE)
        outfile.write(first.read(PNG_IHDR_SIZE))
    # write APNG acTL structure
    outfile.write(struct.pack("!I", 8)) # size
    chunk = "acTL"
    chunk += struct.pack("!I", len(inpaths))
    chunk += struct.pack("!I", 0)
    outfile.write(chunk)
    # CRC
    outfile.write(struct.pack("!i", zlib.crc32(chunk)))
    # write frames
    frame_num = 0
    for inpath in inpaths:
        # write APNG fcTL structure
        outfile.write(struct.pack("!I", 26))
        chunk = "fcTL"
        chunk += struct.pack("!I", frame_num)
        # write frame data from PNG
        with open(inpath) as infile:
            # width, height
            infile.seek(PNG_HEADER_SIZE)
            ihdr = infile.read(PNG_IHDR_SIZE)
            size_start = 8
            size_end = 16
            chunk += ihdr[size_start:size_end]
            # x_offset, y_offset
            chunk += struct.pack("!I", 0)
            chunk += struct.pack("!I", 0)
            # delay_num, delay_den
            chunk += struct.pack("!H", 1000)
            chunk += struct.pack("!H", 1000)
            # dispose_op, blend_op
            chunk += struct.pack("!b", 0)
            chunk += struct.pack("!b", 0)
            outfile.write(chunk)
            outfile.write(struct.pack("!i", zlib.crc32(chunk)))
            # sequence num + data
            data_len = 0
            if frame_num == 0:
                chunk = "IDAT"
                while True:
                    size = seek_IDAT(infile)
                    if size == 0:
                        outfile.write(struct.pack("!I", data_len))
                        outfile.write(chunk)
                        outfile.write(struct.pack("!i", zlib.crc32(chunk)))
                        break
                    chunk += infile.read(size)
                    data_len += size
                    infile.seek(4, 1)
                frame_num += 1
            else:
                chunk = 'fdAT'
                chunk += struct.pack("!I", frame_num+1)
                while True:
                    length = seek_IDAT(infile)
                    if length == 0:
                        outfile.write(struct.pack("!I", data_len+4))
                        outfile.write(chunk)
                        outfile.write(struct.pack("!i", zlib.crc32(chunk)))
                        break
                    chunk += infile.read(length)
                    data_len += length
                    infile.seek(4, 1)
                frame_num += 2
    # write PNG IEND
    outfile.write(struct.pack("!I", 0))
    chunk = PNG_IEND
    outfile.write(chunk)
    outfile.write(struct.pack("!i", zlib.crc32(chunk)))
    outfile.close()

if __name__ == "__main__":
    sys.exit(pngs2apng(*sys.argv[1:]))
