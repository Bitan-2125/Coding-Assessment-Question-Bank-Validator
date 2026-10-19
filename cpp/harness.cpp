// C++ test harness — compiled together with a candidate solution file.
// Protocol: each test case is one line of JSON on stdin; output is one line per case.
// Build: g++ -std=c++17 -O2 -o harness harness.cpp candidate.cpp
//
// Each problem has a dispatcher keyed by problem ID string.
// The harness reads: {"problem":"DSA001","args":[...]}  and writes the result as JSON.

#include <algorithm>
#include <climits>
#include <deque>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std;

// ── tiny JSON helpers ────────────────────────────────────────────────────────

static string trim(const string& s){
    size_t a=s.find_first_not_of(" \t\r\n");
    if(a==string::npos) return "";
    size_t b=s.find_last_not_of(" \t\r\n");
    return s.substr(a,b-a+1);
}

// Parse a flat JSON integer array like [1,2,-3]
static vector<int> parseIntArray(const string& s){
    vector<int> v;
    string inner=s;
    size_t l=inner.find('['), r=inner.rfind(']');
    if(l==string::npos||r==string::npos) return v;
    inner=inner.substr(l+1,r-l-1);
    stringstream ss(inner);
    string tok;
    while(getline(ss,tok,',')){
        tok=trim(tok);
        if(!tok.empty()) v.push_back(stoi(tok));
    }
    return v;
}

// Parse a 2-D integer array like [[1,3],[2,6]] or []
static vector<vector<int>> parse2DIntArray(const string& raw){
    vector<vector<int>> result;
    // find outer '[' then scan for inner '[' ... ']' pairs
    size_t outer=raw.find('[');
    if(outer==string::npos) return result;
    size_t i=outer+1;
    while(i<raw.size()){
        size_t l=raw.find('[',i);
        if(l==string::npos) break;
        // find matching ']'
        int depth=0; size_t r=l;
        for(size_t j=l;j<raw.size();++j){
            if(raw[j]=='[') depth++;
            else if(raw[j]==']'){ depth--; if(depth==0){r=j;break;} }
        }
        string sub=raw.substr(l,r-l+1);
        result.push_back(parseIntArray(sub));
        i=r+1;
    }
    return result;
}

// Parse a quoted JSON string like "hello world"
static string parseString(const string& s){
    size_t a=s.find('"'), b=s.rfind('"');
    if(a==string::npos||a==b) return "";
    string out;
    auto appendUtf8 = [&](unsigned cp){
        if(cp < 0x80) out += char(cp);
        else if(cp < 0x800){ out += char(0xc0|(cp>>6)); out += char(0x80|(cp&63)); }
        else if(cp < 0x10000){ out += char(0xe0|(cp>>12)); out += char(0x80|((cp>>6)&63)); out += char(0x80|(cp&63)); }
        else { out += char(0xf0|(cp>>18)); out += char(0x80|((cp>>12)&63)); out += char(0x80|((cp>>6)&63)); out += char(0x80|(cp&63)); }
    };
    for(size_t i=a+1;i<b;++i){
        if(s[i]!='\\'){ out += s[i]; continue; }
        char escaped=s[++i];
        if(escaped=='u'){
            unsigned cp=stoul(s.substr(i+1,4),nullptr,16); i+=4;
            if(cp>=0xd800 && cp<=0xdbff && i+6<b && s[i+1]=='\\' && s[i+2]=='u'){
                unsigned low=stoul(s.substr(i+3,4),nullptr,16);
                if(low>=0xdc00 && low<=0xdfff){ cp=0x10000+((cp-0xd800)<<10)+(low-0xdc00); i+=6; }
            }
            appendUtf8(cp);
        } else if(escaped=='n') out+='\n';
        else if(escaped=='t') out+='\t';
        else if(escaped=='r') out+='\r';
        else if(escaped=='b') out+='\b';
        else if(escaped=='f') out+='\f';
        else out+=escaped;
    }
    return out;
}

// Parse a JSON integer
static int parseInt(const string& s){ return stoi(trim(s)); }

// ── JSON output helpers ──────────────────────────────────────────────────────

static string toJson(int v){ return to_string(v); }
static string toJson(long long v){ return to_string(v); }
static string toJson(bool v){ return v?"true":"false"; }
static string toJson(const vector<int>& v){
    string s="[";
    for(size_t i=0;i<v.size();++i){ if(i) s+=","; s+=to_string(v[i]); }
    return s+"]";
}
static string toJson(const vector<long long>& v){
    string s="[";
    for(size_t i=0;i<v.size();++i){ if(i) s+=","; s+=to_string(v[i]); }
    return s+"]";
}
static string toJson(const vector<vector<int>>& v){
    string s="[";
    for(size_t i=0;i<v.size();++i){ if(i) s+=","; s+=toJson(v[i]); }
    return s+"]";
}

// ── arg extraction: pull the n-th top-level value from a JSON array string ──

// Returns substring of the n-th element (0-indexed) from a JSON array string.
// Correctly skips over quoted strings so brackets inside quotes are ignored.
static string nthArg(const string& arr, int n){
    // arr looks like: [val0, val1, val2]
    size_t pos=arr.find('[');
    if(pos==string::npos) return "";
    pos++; // skip outer '['
    int depth=0, idx=0;
    size_t start=pos;
    for(size_t i=pos;i<arr.size();++i){
        char c=arr[i];
        if(c=='"'){
            // skip entire quoted string
            ++i;
            while(i<arr.size() && arr[i]!='"'){
                if(arr[i]=='\\') ++i; // escaped char
                ++i;
            }
            // i now points at closing '"'
        } else if(c=='['||c=='{'){
            depth++;
        } else if(c==']'||c=='}'){
            if(depth==0){
                // end of outer array
                if(idx==n) return trim(arr.substr(start,i-start));
                break;
            }
            depth--;
        } else if(c==','&&depth==0){
            if(idx==n) return trim(arr.substr(start,i-start));
            idx++;
            start=i+1;
        }
    }
    return "";
}

// ── forward declarations (implemented in candidate/reference file) ───────────

vector<int>         twoSum(const vector<int>&, int);
bool                isAnagram(const string&, const string&);
int                 binarySearch(const vector<int>&, int);
long long           maxSubarray(const vector<int>&);
int                 maxStockProfit(const vector<int>&);
int                 longestUniqueSubstring(const string&);
bool                isBalanced(const string&);
vector<long long>   productExceptSelf(const vector<int>&);
int                 missingNumber(const vector<int>&);
vector<vector<int>> mergeIntervals(vector<vector<int>>);

// ── dispatcher ───────────────────────────────────────────────────────────────

static string dispatch(const string& problem, const string& args){
    if(problem=="DSA001"){
        auto nums=parseIntArray(nthArg(args,0));
        int target=parseInt(nthArg(args,1));
        return toJson(twoSum(nums,target));
    }
    if(problem=="DSA002"){
        string s=parseString(nthArg(args,0));
        string t=parseString(nthArg(args,1));
        return toJson(isAnagram(s,t));
    }
    if(problem=="DSA005"){
        auto nums=parseIntArray(nthArg(args,0));
        int target=parseInt(nthArg(args,1));
        return toJson(binarySearch(nums,target));
    }
    if(problem=="DSA007"){
        auto nums=parseIntArray(nthArg(args,0));
        return toJson(maxSubarray(nums));
    }
    if(problem=="DSA008"){
        auto prices=parseIntArray(nthArg(args,0));
        return toJson(maxStockProfit(prices));
    }
    if(problem=="DSA009"){
        string s=parseString(nthArg(args,0));
        return toJson(longestUniqueSubstring(s));
    }
    if(problem=="DSA010"){
        string s=parseString(nthArg(args,0));
        return toJson(isBalanced(s));
    }
    if(problem=="DSA012"){
        auto nums=parseIntArray(nthArg(args,0));
        return toJson(productExceptSelf(nums));
    }
    if(problem=="DSA014"){
        auto nums=parseIntArray(nthArg(args,0));
        return toJson(missingNumber(nums));
    }
    if(problem=="DSA020"){
        auto intervals=parse2DIntArray(nthArg(args,0));
        return toJson(mergeIntervals(intervals));
    }
    return "\"UNKNOWN_PROBLEM\"";
}

// ── main ─────────────────────────────────────────────────────────────────────

int main(){
    string line;
    while(getline(cin,line)){
        line=trim(line);
        if(line.empty()) continue;
        // parse {"problem":"DSAxxx","args":[...]}
        size_t pStart=line.find("\"problem\"")+9;
        pStart=line.find('"',pStart)+1;
        size_t pEnd=line.find('"',pStart);
        string problem=line.substr(pStart,pEnd-pStart);

        size_t aStart=line.find("\"args\"")+6;
        aStart=line.find('[',aStart);
        // find matching ']' — must skip quoted strings
        int depth=0; size_t aEnd=aStart;
        for(size_t i=aStart;i<line.size();++i){
            char c=line[i];
            if(c=='"'){
                ++i;
                while(i<line.size()&&line[i]!='"'){
                    if(line[i]=='\\') ++i;
                    ++i;
                }
            } else if(c=='['){
                depth++;
            } else if(c==']'){
                depth--;
                if(depth==0){ aEnd=i; break; }
            }
        }
        string args=line.substr(aStart,aEnd-aStart+1);

        cout<<dispatch(problem,args)<<"\n";
    }
    return 0;
}
