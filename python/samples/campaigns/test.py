from UserCode.VJJSkimmer.samples.campaigns.Manager import Manager as CampaignManager
from UserCode.VJJSkimmer.samples.Sample import Sample
ds='/DoubleEG/Run2016G-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD'
campaign = CampaignManager('DoubleEGData_all')
ds_name='/DoubleEG/Run2016H-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD'
#s_=campaign.get_dataset_info(ds_name)
s=campaign.get_dataset_info(ds)
#print s_.keys()
print s.keys()
