#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import math
import sys
import os
import shutil
import itertools
import yoda

class Bin:
	def __init__(self,values,special=""):
		self.xlow = values[0]
		self.xhigh = values[1]
		self.sumw = values[2]
		self.sumw2 = values[3]
		self.sumwx = values[4]
		self.sumwx2 = values[5]
		self.numEntries = values[6]
		self.special = special

class Histogram:
	def __init__(self,title,path,info,htype,bins):
		self.title = title
		self.path = path
		self.info = info
		self.htype = htype
		self.bins = bins

class Legend:
	def __init__(self,title,nicename,color):
		self.title = title
		self.nicename = nicename
		self.color = color

def fetch(filename):
	if len(filename)<1:
		print "You did not provide a filename!"
		return []
	return yoda.readYODA(filename)

def fetch_plane(filename):
	if len(filename)<1:
		print "You did not provide a filename!"
		return 0
	f = open(filename,'r')	

	hist = False
	binbool = False
	bins = []
	ret = []
	
	for line in f:			
		if line.find("# BEGIN YODA_HISTO1D")>-1:
			title = ""
			htype = ""
			path = ""
			info = ""
			hist = True
		elif line.find("# END YODA_HISTO1D")>-1:
			ret.append(Histogram(title,path,info,htype,bins))
			binbool  = False
		elif line.find("Path=")>-1:
			path = line.replace("Path=","")
		elif line.find("Title=")>-1:
			title = line.replace("Title=","")
		elif line.find("Type=")>-1:
			htype = line.replace("Type=","")
		elif line.find("# xlow")>-1:
			bins = []
			binbool = True
		elif binbool:
			vals = []
			special = ""
			for t in line.split():
				try:
					vals.append(float(t))
				except:
					vals.append(-1)
					if special == "":
						special = t
			bins.append(Bin(vals,special))	
	return ret

def sanitiseString(s):
	s = s.replace('#','\\#')
	s = s.replace('%','\\%')
	return s

def parseArgs(args):
	filelist = []
	plotoptions = {}
	for a in args:
		asplit = a.split(':')
		path = asplit[0]
		filelist.append(path)
		plotoptions[path] = []
		has_title = False
		for i in xrange(1, len(asplit)):
			## Add 'Title' if there is no = sign before math mode
			if not '=' in asplit[i] or ('$' in asplit[i] and asplit[i].index('$') < asplit[i].index('=')):
			    asplit[i] = 'Title=%s' % asplit[i]
			if asplit[i].startswith('Title='):
			    has_title = True
			plotoptions[path].append(asplit[i])
		if not has_title:
			plotoptions[path].append('Title=%s' %sanitiseString(path.split('/')[-1].replace('.yoda', '')))
	return filelist, plotoptions

def getCommandLineOptions():
	from optparse import OptionParser, OptionGroup
	parser = OptionParser(usage=__doc__)
	parser.add_option("-y","--logy", dest="LOGY", action="store_true",
						default=False, help="Logarithmic y-axis")
	parser.add_option("-x","--logx", dest="LOGX", action="store_true",
						default=False, help="Logarithmic x-axis")
	parser.add_option("-o","--overlay", dest="OVERLAY", action="store_true",
						default=False, help="Overlay histograms with equal names")
	parser.add_option("--title", dest="SINGLETITLE",
						default="", help="Plot only the histogram with this title")
	parser.add_option("-n","--no-normal", dest="NORM",action="store_false",
						default=True, help="Do not normalize histograms to 1")
	parser.add_option("--legend", dest="LEGEND",
						default="", help="Provide (optional) legend file in .xml format")
	parser.add_option("--make-legend", dest="MAKELEGEND", action="store_true",
						default=False, help="Make template .xml legend file from .yoda file(s). No plots are produced. ")
	parser.add_option("--no-bind", dest="NOBIND", action="store_true",
						default=False, help="Set if YODA bindings are not installed. Will try to read the flat file. ")
	return parser

def makeLegend(filelist,singlehisto=""):
	for f in filelist:
		name = f.replace(".yoda","")
		legfile = open(name+'.xml',"w")
		histograms = fetch(name+'.yoda' if name.find(".yoda")<0 else name)
		for h in histograms:
			if singlehisto=="" or h.title==singlehisto:
				legfile.write("<legend>\n")
				legfile.write("\t<title=\""+h.title.strip()+"\">\n")
				legfile.write("\t<nicename=\"\">\n")
				legfile.write("\t<color=\"\">\n")
				legfile.write("</legend>\n")
		legfile.close()

def readLegend(filename):
	ret = []
	try:
		legfile = open(filename+'.xml' if filename.find(".xml")<0 else filename)
	except:
		print "COULD NOT OPEN LEGEND-FILE!"
		return ret
	title = ""
	nicename = ""
	color = ""

	for line in legfile:
		if line.find("</legend>")>-1:
			ret.append(Legend(title,nicename,color))
		elif line.find("<legend>")>-1:
			title = ""
			nicename = ""
			color = ""
		elif line.find("<title="):
			title = line[line.find("\"")+1:line.rfind("\"")]
		elif line.find("<nicename="):
			nicename = line[line.find("\"")+1:line.rfind("\"")]
		elif line.find("<color="):
			color = line[line.find("\"")+1:line.rfind("\"")]
	return ret

parser = getCommandLineOptions()
opts, args = parser.parse_args()

filelist, plotopt = parseArgs(args)

plotallhistos = False

if opts.SINGLETITLE=="":
	plotallhistos=True

if len(sys.argv)<2:
	print "Please provide arguments!"

if opts.MAKELEGEND:
	makeLegend(filelist,opts.SINGLETITLE)


for f in filelist:
	name = f
	histograms = []
	if opts.NOBIND:
		histograms = fetch_plane(name+'.yoda' if name.find(".yoda")<0 else name)
	else:
		histograms = fetch(name+'.yoda' if name.find(".yoda")<0 else name)

	fig = 0
	for h in histograms:
		fig += 1
		if plotallhistos or h.title.find(opts.SINGLETITLE)>-1:
			centers = []
			widths = []
			sumw = []
			sumw2 = []
			for bin in h:
				centers.append(bin.midpoint)
				widths.append(bin.width)
				sumw.append(bin.sumW)
				sumw2.append(bin.sumW2) 
			yerr = map(lambda x: math.sqrt(x), sumw2)
			if opts.LOGY:
				plt.set_yscale("log")
			if opts.LOGX:
				plt.set_xscale("log")
			thislegend = Legend(h.title,h.title,"green")
			if opts.LEGEND!="":
				leg = readLegend(opts.LEGEND)
				for l in leg:
					if l.title==h.title:
						thislegend=l
			#ax.errorbar(centers, sumw, yerr=yerr, xerr=widths, fmt='o')
			plt.figure(fig)
			plt.hist(centers,bins=len(centers),weights=sumw,normed=opts.NORM,facecolor=thislegend.color,alpha=0.5)
			plt.title(thislegend.nicename)

	
	plt.show()
