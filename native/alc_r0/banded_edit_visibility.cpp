// Fixture-only trusted CPU analysis. No allocator-owned memory crosses the ABI.
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include "alc_r0_build_id.h"

#define API extern "C" __declspec(dllexport) uint32_t __cdecl
API aluclu_banded_abi_v1() { return 1; }
API aluclu_banded_build_id_v1(uint8_t* out, uint32_t capacity) {
    if (!out || capacity < 32) return 1;
    std::memcpy(out, ALC_R0_BUILD_ID, 32); return 0;
}
static int floor2(int v) { return v >= 0 ? v / 2 : -((-v + 1) / 2); }
static uint32_t signature(uint32_t bits, uint32_t flag) {
    if (flag == 2) return ((bits & 5) ? 4 : 0) | ((bits & 10) ? 8 : 0);
    if (flag == 1) return ((bits & 3) ? 2 : 0) | ((bits & 12) ? 8 : 0);
    return bits;
}
static void wide(uint32_t* out, unsigned slot, uint64_t v) {
    out[slot] = uint32_t(v); out[slot + 1] = uint32_t(v >> 32);
}
API aluclu_banded_audit_v1(const uint32_t* first, uint32_t n,
    const uint32_t* second, uint32_t m, const uint32_t* budgets,
    uint32_t B, uint32_t K, const uint32_t* policy, uint8_t* workspace,
    uint64_t capacity, uint32_t* output, uint32_t output_words) {
    // All transport rejection paths precede any caller-memory write.
    if (!policy || !budgets || !output || output_words < 64 || B < 1 || B > 5
        || (n && !first) || (m && !second)
        || !policy[0] || policy[0] > 32768 || !policy[1] || policy[1] > 4194304
        || !policy[2] || policy[2] > 67108864 || policy[3] > 512 || K > policy[3]
        || !policy[4] || policy[4] > 4096 || !policy[5] || policy[5] > 4096
        || policy[6] > 65536 || (!policy[6] && (n || m)) || policy[7]
        || (workspace && reinterpret_cast<uintptr_t>(workspace) % 4)
        || (!workspace && capacity)) return 1;
    const uint32_t saturation = std::max(std::max(n, m), uint32_t(1));
    for (uint32_t b = 0; b < B; ++b)
        if (!budgets[b] || budgets[b] > saturation || (b && budgets[b] < budgets[b-1])) return 1;
    uint32_t out[64] = {};
    out[0]=1; out[3]=n; out[4]=m; out[5]=B; out[6]=K;
    uint32_t reason=0, width=0; uint64_t cells=0, payload=0, scratch=0;
    int lower=0, upper=0, delta=0;
    if (std::max(n,m)>policy[0]) reason=1;
    else if (std::abs(delta=int(n)-int(m))>int(K)) { reason=2; out[7]=12; }
    else {
        lower=-floor2(int(K)-delta); upper=floor2(delta+int(K));
        for (int i=0;i<=int(n);++i) {
            int low=std::max(0,i-upper), high=std::min(int(m),i-lower);
            uint32_t w=uint32_t(std::max(0,high-low+1)); cells+=w; width=std::max(width,w);
        }
        const uint32_t states=1+7*B;
        payload=uint64_t(2)*states*4*width+uint64_t(B)*(uint64_t(n)+m);
        scratch=payload+uint64_t(2)*states*policy[4]+uint64_t(2)*B*policy[5]+65536;
        out[7]=31; out[8]=uint32_t(lower); out[9]=uint32_t(upper);
        wide(out,10,cells); out[14]=width; wide(out,15,scratch);
        if(cells>policy[1]) reason=3;
        else if(scratch>policy[2] || payload>67108864) reason=4;
    }
    if(reason) { out[1]=1;out[2]=reason;std::memcpy(output,out,sizeof(out));return 0; }
    if(!workspace || capacity<payload || payload>SIZE_MAX) return 2;
    for(uint32_t i=0;i<n;++i) if(first[i]>=policy[6]) return 1;
    for(uint32_t j=0;j<m;++j) if(second[j]>=policy[6]) return 1;
    const uint32_t states=1+7*B, inf=n+m+1;
    uint32_t* previous=reinterpret_cast<uint32_t*>(workspace);
    uint32_t* current=previous+uint64_t(states)*width;
    uint8_t* masks=workspace+uint64_t(2)*states*4*width;
    for(uint32_t b=0;b<B;++b) {
        for(uint32_t p=0;p<n+m;++p) {
            uint32_t len=p<n?n:m, pos=p<n?p:p-n, budget=budgets[b];
            masks[uint64_t(b)*(n+m)+p]=uint8_t(budget>=len || pos<(budget+1)/2 || pos>=len-budget/2);
        }
    }
    int prev_low=0,prev_high=-1; uint64_t visited=0;
    struct Candidate { uint32_t cost; uint32_t* row; uint32_t index; uint32_t operation; };
    for(int i=0;i<=int(n);++i) {
        const int low=std::max(0,i-upper),high=std::min(int(m),i-lower);
        for(int j=low;j<=high;++j) {
            const uint32_t col=uint32_t(j-low); ++visited; current[col]=inf;
            for(uint32_t b=0;b<B;++b) {
                const uint32_t offset=1+7*b;
                for(uint32_t s=0;s<6;++s) current[uint64_t(offset+s)*width+col]=(s%2)?0:inf;
                current[uint64_t(offset+6)*width+col]=0;
            }
            if(!i&&!j) {
                current[col]=0;
                for(uint32_t b=0;b<B;++b) {
                    for(uint32_t s=0;s<6;++s) current[uint64_t(1+7*b+s)*width+col]=0;
                    current[uint64_t(7+7*b)*width+col]=1;
                } continue;
            }
            Candidate candidates[3]; uint32_t count=0;
            if(i && prev_low<=j && j<=prev_high && previous[j-prev_low]<inf)
                candidates[count++]={previous[j-prev_low]+1,previous,uint32_t(j-prev_low),2};
            if(j>low && current[col-1]<inf) candidates[count++]={current[col-1]+1,current,col-1,1};
            if(i&&j&&prev_low<=j-1&&j-1<=prev_high&&first[i-1]==second[j-1]&&previous[j-1-prev_low]<inf)
                candidates[count++]={previous[j-1-prev_low],previous,uint32_t(j-1-prev_low),0};
            uint32_t distance=inf;
            for(uint32_t c=0;c<count;++c) distance=std::min(distance,candidates[c].cost);
            current[col]=distance;
            for(uint32_t b=0;b<B;++b) for(uint32_t c=0;c<count;++c) {
                const Candidate& pred=candidates[c]; if(pred.cost!=distance) continue;
                uint32_t left=pred.operation==2?masks[uint64_t(b)*(n+m)+i-1]:0;
                uint32_t right=pred.operation==1?masks[uint64_t(b)*(n+m)+n+j-1]:0;
                uint32_t additions[3]={left,right,left+right},offset=1+7*b;
                for(uint32_t obj=0;obj<3;++obj) {
                    uint64_t s=uint64_t(offset+2*obj)*width;
                    current[s+col]=std::min(current[s+col],pred.row[s+pred.index]+additions[obj]);
                    current[s+width+col]=std::max(current[s+width+col],pred.row[s+width+pred.index]+additions[obj]);
                }
                uint64_t s=uint64_t(offset+6)*width;
                current[s+col]|=signature(pred.row[s+pred.index],left?2:right?1:0);
            }
        }
        std::swap(previous,current);prev_low=low;prev_high=high;
    }
    if(visited!=cells || int(m)<prev_low || int(m)>prev_high) return 3;
    uint32_t terminal=m-uint32_t(prev_low),distance=previous[terminal];
    wide(out,12,visited);wide(out,17,payload);
    if(distance>K) {out[1]=1;out[2]=2;}
    else {
        out[7]|=32;out[19]=distance;
        for(uint32_t b=0;b<B;++b) for(uint32_t s=0;s<7;++s)
            out[20+7*b+s]=previous[uint64_t(1+7*b+s)*width+terminal];
    }
    std::memcpy(output,out,sizeof(out));return 0;
}
