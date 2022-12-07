from UserCode.VJJSkimmer.samples.Sample import Sample
from UserCode.VJJSkimmer.samples.Manager import currentSampleList
for year in ['2016','2017','2018']:
    f = open('sample_'+year,'w')
    for s,info in currentSampleList.all_datasets():
        n = Sample(s)
        if str(info['year']) in year:
           f.write('-d {0} -y {1}\n'.format(s,year))
#           print(year,s,info['year'])
 
