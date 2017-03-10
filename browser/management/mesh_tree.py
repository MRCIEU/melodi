# reads data from mesh asci file and creates mesh tree graph
# data from here - ftp://nlmpubs.nlm.nih.gov/online/mesh/.asciimesh/d2016.bin
# label descriptions here - https://www.nlm.nih.gov/mesh/dtype.html
# extracts Mesh Heading (MH), Mesh Tree Number (MN) and Unique Identifier (UI)

#from browser.models import MeshTerm

import os

def run(meshFile,outDir):
	#parse file once to make dictionary of headers and tree id
	mDic = dict()
	with open(meshFile, 'r') as f:
		for line in f:
			if line[0:3] == "MH ":
				mTree = "None"
				mName = line.split("=", 1)[1].strip()
			elif line[0:3] == "MN ":
				mTree = line.split("=", 1)[1].strip()
				mDic[mTree]=mName

	#read dictionary and create graph data
	n = open(os.path.join(outDir,'meshTreeNodes.txt'), 'w')
	r = open(os.path.join(outDir,'meshTreeRels.txt'), 'w')
	for i in mDic:
		n.write(i+"|"+mDic[i]+"\n")
		#print i,mDic[i]
		parent = i[:-4]
		#print parent
		if parent in mDic:
			r.write(parent+"|"+i+"\n")
		else:
			r.write("None|"+i+"\n")

	#write the remaining files
	nHead = open(os.path.join(outDir,'meshTreeNodes_header.txt'), 'w')
	rHead = open(os.path.join(outDir,'meshTreeRels_header.txt'), 'w')
	nHead.write('tree_id:ID(MeshTree)|mesh_name')
	rHead.write(':END_ID(MeshTree)|:START_ID(MeshTree)')

run('d2016.bin','mesh/')