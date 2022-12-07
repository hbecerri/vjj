from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.Manager import currentSampleList
import sys
for year in ['2016','2017','2018']:
    f = open('sample_'+year,'w')
    for s,info in currentSampleList.all_datasets():
        n = Sample(s)
        if str(info['year']) in year and (sys.argv[1] in s or sys.argv[2] in s):
           f.write('{0}\n'.format(s))
           print(year,s,info['year'],info['signal'])
 
