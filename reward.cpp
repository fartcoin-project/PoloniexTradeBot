/*
To compile:  g++ -std=gnu++11 reward.cpp -o reward
*/

#include <iostream>
#include <cstdint>
#include <cinttypes>

using namespace std;

template <class TblockValue>
class nHeightDivided {
    private:
        TblockValue firstValue, secondValue;
    public:
        nHeightDivided (TblockValue a, TblockValue b):
        firstValue(a), secondValue(b) { }
        TblockValue devideValue();
};

template <class TblockValue>
TblockValue nHeightDivided<TblockValue>::devideValue() {
    return (firstValue/secondValue);
}

template <class UblockValue, class VblockValue>
UblockValue SubsidyValue(UblockValue a, VblockValue b) {
    return (a / b);
}







int main()
{
    int64_t count = 0;
    int64_t j;
    cout<< "enter total blocks\n";
    cin >> j;
   		
    for (int64_t i = 1;i<j+1;i++ ) {
        int64_t nHeight = i; 
        int64_t COIN = 100000000;    
	int64_t nSubsidy = 1 * COIN;    
	
        if(nHeight < 11)
        {
            int64_t minsub = 1000000 * COIN;
            nHeightDivided <double> obj(nHeight, 10);
            double heightresult = obj.devideValue();
            int64_t nSubsidy = SubsidyValue(minsub,heightresult);
            count+=nSubsidy; 

	    if(nHeight == 1){
            cout << "Block    " << i << " subsidy = " << minsub << "/(   " << nHeight << "/  10) = "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	    }
	    else if(nHeight < 10){
            cout << "Block    " << i << " subsidy = " << minsub << "/(   " << nHeight << "/  10) =  "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	    }
            if(nHeight == 10){
            cout << "Block   " << i << " subsidy = " << minsub << "/(  " << nHeight << "/  10) =  "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	     
            }
        }
       
        else if (nHeight < 101){ 
            int64_t minsub = 100000 * COIN;
            nHeightDivided <double> obj(nHeight, 100);
            double heightresult = obj.devideValue();
            int64_t nSubsidy = SubsidyValue(minsub,heightresult);
            count+=nSubsidy; 
            if(nHeight < 100){
            cout << "Block   " << i << " subsidy =  " << minsub << "/(  " << nHeight << "/ 100) =   "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	    }
            if(nHeight == 100){
            cout << "Block  " << i << " subsidy =  " << minsub << "/( " << nHeight << "/ 100) =   "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	       	    
            }                    
        }
        
	else if (nHeight < 1001){ 
            int64_t minsub = 10000 * COIN;
            nHeightDivided <double> obj(nHeight, 1000);
            double heightresult = obj.devideValue();
            int64_t nSubsidy = SubsidyValue(minsub,heightresult);
            count+=nSubsidy; 
            if(nHeight < 1000){
            cout << "Block  " << i << " subsidy =   " << minsub << "/( " << nHeight << "/1000) =    "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	    }
            if(nHeight == 1000){
            cout << "Block " << i << " subsidy =   " << minsub << "/(" << nHeight << "/1000) =    "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	        	                
            }                           	   
        }
	else if (nHeight < 10001){ 
            int64_t minsub = 1000 * COIN;
            nHeightDivided <double> obj(nHeight, 10000);
            double heightresult = obj.devideValue();
            int64_t nSubsidy = SubsidyValue(minsub,heightresult);
            count+=nSubsidy; 
            if(nHeight < 10000){
            cout << "Block " << i << " subsidy =    " << minsub << "/( " << nHeight << "/10000) =   "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	    }
            if(nHeight == 10000){
            cout << "Block" << i << " subsidy =    " << minsub << "/(" << nHeight << "/10000) =   "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	       	                
            }                           	   
        }
	else if (nHeight < 100001){ 
            int64_t minsub = 100 * COIN;
            nHeightDivided <double> obj(nHeight, 100000);
            double heightresult = obj.devideValue();
            int64_t nSubsidy = SubsidyValue(minsub,heightresult);
            count+=nSubsidy; 
            if(nHeight < 100000){
            cout << "Block " << i << " subsidy =    " << minsub << "/(" << nHeight << "/100000)=    "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	    }
            if(nHeight == 100000){
            cout << "Block" << i << " subsidy =    " << minsub << "/(" << nHeight << "/100000)=   "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	       	                
            }                           	   
        }
	else if (nHeight < 1000001){ 
            int64_t minsub = 10 * COIN;
            nHeightDivided <double> obj(nHeight, 1000000);
            double heightresult = obj.devideValue();
            int64_t nSubsidy = SubsidyValue(minsub,heightresult);
            count+=nSubsidy; 
            if(nHeight < 1000000){
            cout << "Block " << i << " subsidy =    " << minsub << "/(" << nHeight << "/1000000) =  "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	    }
            if(nHeight == 1000000){
            cout << "Block " << i << " subsidy =   " << minsub << "/(" << nHeight << "/1000000)=  "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	        	                
            }                           	   
        }
	else if (nHeight < 10000001){ 
            int64_t minsub = 1 * COIN;
            nHeightDivided <double> obj(nHeight, 10000000);
            double heightresult = obj.devideValue();
            int64_t nSubsidy = SubsidyValue(minsub,heightresult);
            count+=nSubsidy; 
            if(nHeight < 10000000){
            cout << "Block " << i << " subsidy =    " << minsub << "/(" << nHeight << "/10000000)=  "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	    }
            if(nHeight == 10000000){
            cout << "Block " << i << " subsidy=    " << minsub << "/(" << nHeight << "/10000000)=  "<< nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
    	       	                
            }                           	   
        }

        else {
            cout << "Block " << i << " subsidy = " << nSubsidy / 100000000 << "." << nSubsidy % 100000000<< '\n';
        }
        
    };//End for()
    cout << "************************************************************************************************" << '\n';
    cout << '\n';  
    cout << "Total Fartcoins generated after " << j << " blocks = " << count / 100000000 << "." << count % 100000000 << '\n';
    
return 0;
}
