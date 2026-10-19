// Reference implementations for selected DSA problems. Compile check: g++ -std=c++17 -Wall -Wextra -pedantic -c cpp/reference_solutions.cpp
#include <algorithm>
#include <climits>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std;
vector<int> twoSum(const vector<int>& nums, int target) {
    unordered_map<long long,int> seen;
    for(int i=0;i<(int)nums.size();++i){
        auto it=seen.find((long long)target-nums[i]);
        if(it!=seen.end()) return {it->second,i};
        seen[nums[i]]=i;
    }
    return {-1,-1};
}
bool isAnagram(const string& s,const string& t){ if(s.size()!=t.size()) return false; int f[256]={0}; for(unsigned char c:s) ++f[c]; for(unsigned char c:t) --f[c]; for(int x:f) if(x) return false; return true; }
int binarySearch(const vector<int>& a,int target){ int l=0,r=(int)a.size()-1; while(l<=r){ int m=l+(r-l)/2; if(a[m]==target)return m; if(a[m]<target)l=m+1;else r=m-1;} return -1; }
long long maxSubarray(const vector<int>& a){ long long cur=a[0],best=a[0]; for(size_t i=1;i<a.size();++i){cur=max((long long)a[i],cur+a[i]);best=max(best,cur);}return best; }
int maxStockProfit(const vector<int>& p){ int low=INT_MAX,best=0; for(int x:p){low=min(low,x);best=max(best,x-low);}return best; }
int longestUniqueSubstring(const string& s){
    unordered_map<unsigned,int> last;
    int left=0,best=0,index=0;
    for(size_t i=0;i<s.size();){
        unsigned char first=s[i++]; unsigned cp=first; int continuation=0;
        if(first>=0xf0){cp=first&7; continuation=3;}
        else if(first>=0xe0){cp=first&15; continuation=2;}
        else if(first>=0xc0){cp=first&31; continuation=1;}
        while(continuation-- && i<s.size()) cp=(cp<<6)|(s[i++]&63);
        auto it=last.find(cp);
        if(it!=last.end()) left=max(left,it->second+1);
        last[cp]=index; best=max(best,index-left+1); ++index;
    }
    return best;
}
bool isBalanced(const string& s){ vector<char> st; for(char c:s){if(c=='('||c=='['||c=='{')st.push_back(c);else{char need=c==')'?'(':c==']'?'[':c=='}'?'{':'\0';if(need){if(st.empty()||st.back()!=need)return false;st.pop_back();}}}return st.empty(); }
vector<long long> productExceptSelf(const vector<int>& a){
    vector<long long> out(a.size(),0);
    int zeros=count(a.begin(),a.end(),0);
    if(zeros>1) return out;
    if(zeros==1){
        long long product=1;
        for(int x:a) if(x) product*=x;
        for(size_t i=0;i<a.size();++i) if(!a[i]) out[i]=product;
        return out;
    }
    long long prefix=1,suffix=1;
    for(size_t i=0;i<a.size();++i){out[i]=prefix; if(i+1<a.size()) prefix*=a[i];}
    for(size_t i=a.size();i>0;--i){out[i-1]*=suffix; if(i>1) suffix*=a[i-1];}
    return out;
}
int missingNumber(const vector<int>& a){ long long n=a.size(); long long expected=n*(n+1)/2; for(int x:a)expected-=x;return (int)expected; }
vector<vector<int>> mergeIntervals(vector<vector<int>> a){ if(a.empty())return {}; sort(a.begin(),a.end()); vector<vector<int>> out{a[0]}; for(size_t i=1;i<a.size();++i){if(a[i][0]<=out.back()[1])out.back()[1]=max(out.back()[1],a[i][1]);else out.push_back(a[i]);}return out; }
