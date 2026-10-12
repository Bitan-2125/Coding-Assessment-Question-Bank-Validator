"""Reference solutions for DSA001-DSA020. Inputs match question_bank.json test-case args."""
from collections import Counter, defaultdict, deque
import heapq

def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen: return [seen[target-x], i]
        seen[x] = i
    return [-1, -1]

def is_anagram(s, t): return Counter(s) == Counter(t)

def first_unique_char(s):
    c=Counter(s)
    return next((i for i,ch in enumerate(s) if c[ch] == 1), -1)

def move_zeroes(nums):
    out=[x for x in nums if x != 0]
    return out + [0]*(len(nums)-len(out))

def binary_search(nums, target):
    lo,hi=0,len(nums)-1
    while lo<=hi:
        mid=lo+(hi-lo)//2
        if nums[mid]==target: return mid
        if nums[mid]<target: lo=mid+1
        else: hi=mid-1
    return -1

def merge_sorted(a,b):
    i=j=0; out=[]
    while i<len(a) and j<len(b):
        if a[i]<=b[j]: out.append(a[i]); i+=1
        else: out.append(b[j]); j+=1
    return out+a[i:]+b[j:]

def max_subarray(nums):
    best=cur=nums[0]
    for x in nums[1:]: cur=max(x,cur+x); best=max(best,cur)
    return best

def max_stock_profit(prices):
    low=float('inf'); best=0
    for p in prices: low=min(low,p); best=max(best,p-low)
    return best

def longest_unique_substring(s):
    last={}; left=best=0
    for right,ch in enumerate(s):
        if ch in last and last[ch]>=left: left=last[ch]+1
        last[ch]=right; best=max(best,right-left+1)
    return best

def is_balanced(s):
    pairs={')':'(',']':'[','}':'{'}; stack=[]
    for ch in s:
        if ch in '([{': stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop()!=pairs[ch]: return False
    return not stack

def top_k_frequent(nums,k):
    counts=Counter(nums)
    return sorted(counts, key=lambda x:(-counts[x],x))[:k]

def product_except_self(nums):
    out=[1]*len(nums); prefix=1
    for i,x in enumerate(nums): out[i]=prefix; prefix*=x
    suffix=1
    for i in range(len(nums)-1,-1,-1): out[i]*=suffix; suffix*=nums[i]
    return out

def rotate_right(nums,k):
    if not nums: return []
    k%=len(nums)
    return nums[-k:]+nums[:-k] if k else nums[:]

def missing_number(nums):
    n=len(nums)
    return n*(n+1)//2-sum(nums)

def group_anagrams(strs):
    groups=defaultdict(list)
    for s in strs: groups[tuple(sorted(s))].append(s)
    return list(groups.values())

def num_islands(grid):
    if not grid: return 0
    rows,cols=len(grid),len(grid[0]); seen=set(); count=0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c]=='1' and (r,c) not in seen:
                count+=1; stack=[(r,c)]; seen.add((r,c))
                while stack:
                    x,y=stack.pop()
                    for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                        if 0<=nx<rows and 0<=ny<cols and grid[nx][ny]=='1' and (nx,ny) not in seen:
                            seen.add((nx,ny)); stack.append((nx,ny))
    return count

def shortest_path_unweighted(n,edges,source,target):
    graph=[[] for _ in range(n)]
    for u,v in edges: graph[u].append(v); graph[v].append(u)
    dist=[-1]*n; dist[source]=0; q=deque([source])
    while q:
        u=q.popleft()
        if u==target: return dist[u]
        for v in graph[u]:
            if dist[v]==-1: dist[v]=dist[u]+1; q.append(v)
    return -1

def climb_stairs(n):
    a,b=1,1
    for _ in range(n): a,b=b,a+b
    return a

def coin_change(coins,amount):
    dp=[amount+1]*(amount+1); dp[0]=0
    for x in range(1,amount+1):
        for coin in coins:
            if coin<=x: dp[x]=min(dp[x],dp[x-coin]+1)
    return dp[amount] if dp[amount]<=amount else -1

def merge_intervals(intervals):
    if not intervals: return []
    intervals=sorted([list(x) for x in intervals]); out=[intervals[0]]
    for start,end in intervals[1:]:
        if start<=out[-1][1]: out[-1][1]=max(out[-1][1],end)
        else: out.append([start,end])
    return out
