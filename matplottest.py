#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import math
import sys
import os
import shutil
import itertools
import yoda

con = 0
analysisobjects = yoda.readYODA("LHCpp_r04.yoda")
for ao in analysisobjects:
	for bin in ao.bins:
		print bin.sumW 