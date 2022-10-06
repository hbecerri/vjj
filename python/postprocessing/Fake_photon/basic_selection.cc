#include <algorithm>
#include <iterator>
#include <TROOT.h>
#include <TH2.h>
#include <TStyle.h>
#include <TCanvas.h>
#include <TLatex.h>
#include "TCanvas.h"
#include "RooPlot.h"
#include "TTree.h"
#include "TH1D.h"
#include "TH1F.h"
#include "THStack.h"
#include "TRandom.h"
#include "TUnfoldDensity.h"
#include "TGraph.h"
#include "TGraphErrors.h"
#include "TFrame.h"
#include "TPaveLabel.h"
#include "TPad.h"
#include "TLegend.h"
#include "TRandom3.h"

void basic_selection(string var_name = "", string var_gen = "", string region = "", string year = "2016")
{

    gStyle->SetOptStat(0);

//----obetener_toda_la_informacion_de_entrada--------??

    TChain *chreco_SinglePhoton16 = new TChain("Events","");
    chreco_SinglePhoton16->Add("/nfs/dust/cms/user/hugobg/GJets/CMSSW_10_2_13/src/UserCode/VJJSkimmer/python/postprocessing/2016/SinglePhoton_2016_H_v1/*.root/Events");
    TTree *treereco_SinglePhoton16 = (TTree*) chreco_SinglePhoton16;

    TChain *chreco_GJetsNLO16 = new TChain("Events","");
    chreco_GJetsNLO16->Add("/nfs/dust/cms/user/hugobg/GJets/CMSSW_10_2_13/src/UserCode/VJJSkimmer/python/postprocessing/2016/G1Jet_LHEGpT-675ToInf_TuneCP5_13TeV-amcatnlo-pythia8/*.root/Events");
    TTree *treereco_GJetsNLO16 = (TTree*) chreco_GJetsNLO16;

    cout << treereco_SinglePhoton16->GetEntries() << endl;
    cout << treereco_GJetsNLO16->GetEntries() << endl;
 
    Float_t Binning_jjmass[] = {500.,1000.,2000.,4000.};
    Int_t binning_jjmass = sizeof(Binning_jjmass)/sizeof(Float_t) - 1;

    string sub_isloosePU_fail = "(vjj_sublead_isloosePU < 0.)";
    string sub_isloosePU_pass = "(vjj_sublead_isloosePU > 0.)";

    string isHighVPt = "(vjj_isHighVPt == 1)";

    string EE = "(TMath::Abs(vjj_v_eta) >= 1.56 && TMath::Abs(vjj_v_eta) < 2.4)";
    string EB = "(vjj_v_eta <= 1.44)";

    string tight_photons_barrel = "(vjj_a_hoe < 0.02148 && vjj_a_sieie < 0.00996 && vjj_a_pfRelIso03_chg*vjj_v_pt < 0.650)";
    string tight_photons_endcap = "(vjj_a_hoe < 0.03210 && vjj_a_sieie < 0.02710 && vjj_a_pfRelIso03_chg*vjj_v_pt < 0.517)"; 
 
    string not_tight_photons_barrel = "(vjj_a_hoe < 0.04596 && vjj_a_sieie < 0.0133 && (5*1.694 < 0.2*vjj_v_pt ? vjj_a_pfRelIso03_chg*vjj_v_pt < 5*1.694 : vjj_a_pfRelIso03_chg*vjj_v_pt < 0.2*vjj_v_pt))";
    string not_tight_photons_endcap = "(vjj_a_hoe < 0.05900 && vjj_a_sieie < 0.0272 && (5*2.089 < 0.2*vjj_v_pt ? vjj_a_pfRelIso03_chg*vjj_v_pt < 5*2.089 : vjj_a_pfRelIso03_chg*vjj_v_pt < 0.2*vjj_v_pt))";

    string relaxed_tight_photons_barrel = "(vjj_a_hoe < 0.02148 && vjj_a_sieie < 0.05 && vjj_a_pfRelIso03_chg*vjj_v_pt < 0.650)";
    string relaxed_tight_photons_endcap = "(vjj_a_hoe < 0.03210 && vjj_a_sieie < 0.05 && vjj_a_pfRelIso03_chg*vjj_v_pt < 0.517)";
 
    string data_template_tight_photons_barrel = "(vjj_a_hoe < 0.02148 && vjj_a_sieie < 0.05 && vjj_a_pfRelIso03_chg*vjj_v_pt < 40 && vjj_a_pfRelIso03_chg*vjj_v_pt > 0.650)";
    string data_template_tight_photons_endcap = "(vjj_a_hoe < 0.03210 && vjj_a_sieie < 0.05 && vjj_a_pfRelIso03_chg*vjj_v_pt < 40 && vjj_a_pfRelIso03_chg*vjj_v_pt > 0.517)";
 

//========Region D ============?
// subl jet fail PileupId and tightId Photons
  
    TH1F *jj_mass_D_photons_EE = new TH1F("jj_mass_D_photons_EE","",binning_jjmass,Binning_jjmass);
    TH1F *jj_mass_D_photons_EB = new TH1F("jj_mass_D_photons_EB","",binning_jjmass,Binning_jjmass);
 
    treereco_SinglePhoton16->Project("jj_mass_D_photons_EE","vjj_jj_m",Form("%s*%s*%s*%s",isHighVPt.c_str(),tight_photons_endcap.c_str(),EE.c_str(),sub_isloosePU_fail.c_str()));
    treereco_SinglePhoton16->Project("jj_mass_D_photons_EB","vjj_jj_m",Form("%s*%s*%s*%s",isHighVPt.c_str(),tight_photons_barrel.c_str(),EB.c_str(),sub_isloosePU_fail.c_str()));

//===============Region C=============? 
// subl jet fail PileupId and non tightId Photons

    TH1F *jj_mass_C_photons_EE = new TH1F("jj_mass_C_photons_EE","",binning_jjmass,Binning_jjmass);
    TH1F *jj_mass_C_photons_EB = new TH1F("jj_mass_C_photons_EB","",binning_jjmass,Binning_jjmass);

    treereco_SinglePhoton16->Project("jj_mass_C_photons_EB","vjj_jj_m",Form("%s*%s*%s*%s",isHighVPt.c_str(),not_tight_photons_barrel.c_str(),EB.c_str(),sub_isloosePU_fail.c_str()));
    treereco_SinglePhoton16->Project("jj_mass_C_photons_EE","vjj_jj_m",Form("%s*%s*%s*%s",isHighVPt.c_str(),not_tight_photons_endcap.c_str(),EE.c_str(),sub_isloosePU_fail.c_str()));


//========Region A============?
// subl jet pass PileupId and tightId Photons

    TH1F *jj_mass_A_photons_EE = new TH1F("jj_mass_A_photons_EE","",binning_jjmass,Binning_jjmass);
    TH1F *jj_mass_A_photons_EB = new TH1F("jj_mass_A_photons_EB","",binning_jjmass,Binning_jjmass);

    treereco_SinglePhoton16->Project("jj_mass_A_photons_EE","vjj_jj_m",Form("%s*%s*%s*%s",isHighVPt.c_str(),tight_photons_endcap.c_str(),EE.c_str(),sub_isloosePU_pass.c_str()));
    treereco_SinglePhoton16->Project("jj_mass_A_photons_EB","vjj_jj_m",Form("%s*%s*%s*%s",isHighVPt.c_str(),tight_photons_barrel.c_str(),EB.c_str(),sub_isloosePU_pass.c_str()));


//===============Region B=============? 
// subl jet pass PileupId and non tightId Photons

    TH1F *jj_mass_B_photons_EE = new TH1F("jj_mass_B_photons_EE","",binning_jjmass,Binning_jjmass);
    TH1F *jj_mass_B_photons_EB = new TH1F("jj_mass_B_photons_EB","",binning_jjmass,Binning_jjmass);
    
    treereco_SinglePhoton16->Project("jj_mass_B_photons_EB","vjj_jj_m",Form("%s*%s*%s*%s",isHighVPt.c_str(),not_tight_photons_barrel.c_str(),EB.c_str(),sub_isloosePU_pass.c_str()));
    treereco_SinglePhoton16->Project("jj_mass_B_photons_EE","vjj_jj_m",Form("%s*%s*%s*%s",isHighVPt.c_str(),not_tight_photons_endcap.c_str(),EE.c_str(),sub_isloosePU_pass.c_str()));



//data_template_fit
 
    TH1F *Template_Fake_EE = new TH1F("Template_Fake_EE","",20,0,0.05);
    TH1F *Template_Fake_EB = new TH1F("Template_Fake_EB","",20,0,0.05);

    treereco_SinglePhoton16->Project("Template_Fake_EB","vjj_a_sieie",Form("%s*%s*%s*%s",isHighVPt.c_str(),data_template_tight_photons_endcap.c_str(),EB.c_str(),sub_isloosePU_fail.c_str()));
    treereco_SinglePhoton16->Project("Template_Fake_EE","vjj_a_sieie",Form("%s*%s*%s*%s",isHighVPt.c_str(),data_template_tight_photons_barrel.c_str(),EE.c_str(),sub_isloosePU_fail.c_str()));

//G+jets template fit 

    TH1F *Template_Promt_EE = new TH1F("Template_Promt_EE","",20,0,0.05);
    TH1F *Template_Promt_EB = new TH1F("Template_Promt_EB","",20,0,0.05);
 
    treereco_GJetsNLO16->Project("Template_Promt_EB","vjj_a_sieie",Form("%s*%s*%s*%s",isHighVPt.c_str(),EB.c_str(),sub_isloosePU_fail.c_str(),relaxed_tight_photons_endcap.c_str()));
    treereco_GJetsNLO16->Project("Template_Promt_EE","vjj_a_sieie",Form("%s*%s*%s*%s",isHighVPt.c_str(),EE.c_str(),sub_isloosePU_fail.c_str(),relaxed_tight_photons_endcap.c_str()));

//data_fit

    TH1F *DATA_EE = new TH1F("DATA_EE","",20,0,0.05);
    TH1F *DATA_EB = new TH1F("DATA_EB","",20,0,0.05);

    treereco_SinglePhoton16->Project("DATA_EB","vjj_a_sieie",Form("%s*%s*%s*%s",isHighVPt.c_str(),relaxed_tight_photons_endcap.c_str(),EB.c_str(),sub_isloosePU_fail.c_str()));
    treereco_SinglePhoton16->Project("DATA_EE","vjj_a_sieie",Form("%s*%s*%s*%s",isHighVPt.c_str(),relaxed_tight_photons_barrel.c_str(),EE.c_str(),sub_isloosePU_fail.c_str()));


//=======Control_root_files=========================?

    TFile out("Fake_photon_raw.root","recreate");
    jj_mass_A_photons_EE->Write("jj_mass_loose_photons_EE");
    jj_mass_B_photons_EE->Write("jj_mass_tight_photons_EE");
    jj_mass_C_photons_EE->Write("jj_mass_loose_photons_EE");
    jj_mass_D_photons_EE->Write("jj_mass_tight_photons_EE");
    jj_mass_A_photons_EB->Write("jj_mass_loose_photons_EB");
    jj_mass_B_photons_EB->Write("jj_mass_tight_photons_EB");
    jj_mass_C_photons_EB->Write("jj_mass_loose_photons_EB");
    jj_mass_D_photons_EB->Write("jj_mass_tight_photons_EB");
    Template_Fake_EE->Write("Template_Fake_EE");
    Template_Fake_EB->Write("Template_Fake_EB");
    Template_Promt_EE->Write("Template_Promt_EE");
    Template_Promt_EB->Write("Template_Promt_EB");
    DATA_EE->Write("DATA_EE");
    DATA_EB->Write("DATA_EB");


//sieie plot 

    auto cc = new TCanvas("cc","cc");
//    DATA_EB->SetMarkerStyle(22);
//    DATA_EB->SetMarkerSize(1);
//    Template_Fake_EB->SetFillColor(46);
//    Template_Fake_EB->SetFillStyle(4050);
//    Template_Promt_EB->SetFillColor(47);
//    Template_Promt_EB->SetFillStyle(4050);


    Template_Promt_EB->SetLineColor(kGreen);
    DATA_EB->SetLineColor(kRed);

    Template_Promt_EB->Draw();    
    DATA_EB->Draw("same");
    Template_Fake_EB->Draw("same");
//    DATA_EB->Draw("samep");

    cc->SaveAs("PLot.pdf");
 

// template fit


    TObjArray *mctot = new TObjArray(1);   // MC histograms are put in this array
    mctot->Add(Template_Promt_EB);
    mctot->Add(Template_Fake_EB);
 
    TFractionFitter* myfit = new TFractionFitter(DATA_EB, mctot);   // initialize
    myfit->SetRangeX(1,20);					   //choose the number of bins for the fit 
    Int_t status = myfit->Fit();
  
    if (status == 0) {
       TH1F* result = (TH1F*) myfit->GetPlot();
       DATA_EB->Draw("Ep");
       result->Draw("same");
    }	

    cout << status << endl;

}
