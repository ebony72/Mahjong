from utils.xzutils import *

        
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\


def pure(H,Pg,K,numWl):

    index = 0 
    n_major = 0 
    DT = [] 
    outcome = []
    
    if (bool(Pg)==False or (u[0] == Pg[0][0] for u in Pg)) and numWl > 30: 

        A=[]
        B=[]
        A.append(H[0])
        TH = H[:]
        TH.remove(TH[0])
        TH = TH+Pg+Pg+Pg
        
        for t in TH:
            if t[0] == A[0][0]:
                A.append(t)
            else:
                B.append(t)
               
        if len(A)>len(B) and (e[0] != A[0][0] for e in Pg):
            n_major = len(A)
            DT = B[:]
            
        elif len(B)>len(A) and (e[0] != B[0][0] for e in Pg):
            n_major = len(B)
            DT = A[:]
            
        flag1,flag2,flag3=0,0,0 
        
        if n_major >= 10: 
            
            UDT = remove_duplicates(DT)
            UDT.sort(key=lambda t: t[0:2])
            
            for i in range(len(UDT)):
                
                if DT.count(UDT[i]) == 3:
                    flag1 = 1
                    break
                
                if DT.count(UDT[i]) == 2:
                    flag2 = flag2+1
                    
            for i in range(len(UDT)-1):
                
                if UDT[i][1] == UDT[i+1][1]-1 and UDT[i][1] == UDT[i+2][1]-2:
                    flag3 = flag3+1
                    break
                
            if flag1 == 0 or flag2 < 2 or flag3 == 0:                
                index = 1
                outcome = [index,DT]
                
                
            else:
                DT = []
                outcome = [index,DT]
        else:
            DT = []
            outcome = [index,DT]
                           
    else:
        outcome = [index,DT]
        
                       
    return outcome


def sevenpair(H,Pg,K,numWl):
    
    index = 0 
    n_pair = 0 
    DT = [] 
    outcome = []
    
    if bool(Pg) == False:

        UH = remove_duplicates(H)    
        for u in UH:
            
            if H.count(u) >= 2:
                n_pair = n_pair+1
            else:
                DT.append(u)
                
        if n_pair >= 5 and numWl > 30: 
            index = 1
            outcome = [index,DT]
        else:
            DT = []
            outcome = [index,DT]
    else:
        outcome = [index,DT]
                   
    return outcome

def pphu(H,Pg,K,numWl):
    
    index = 0 
    DT = [] 
    outcome = []
    
    UH = remove_duplicates(H)
    n_p0 = len(Pg)
    n_p1,n_p2 = 0,0 
    
    for u in UH:
        if H.count(u)==3:
            n_p1 = n_p1+1
        elif H.count(u)==2:
            n_p2 = n_p2+1
        else:
            DT.append(u)

    if n_p0+n_p1==4 or (n_p0+n_p1==3 and n_p2>1) or (n_p0+n_p1==2 and n_p2>2 and numWl>20):
        index = 1
        outcome = [index,DT]
    else:
        DT = []
        outcome = [index,DT]

    return outcome



def Type(H,Pg,K,numWl):

    TYPE = []
    type1 = pure(H,Pg,K,numWl)
    type2 = sevenpair(H,Pg,K,numWl)
    type3 = pphu(H,Pg,K,numWl)
    TYPE = [type1,type2,type3]

    return TYPE
        


# test
if __name__ == '__main__': 
    H = [[1, 1], [1, 2], [1, 5], [1, 5], [1, 6], [1, 7], [1, 9], [2, 2], [2, 3], [2, 6], [2, 7], [2, 7]]
    Pg = []
    K = [3, 3, 3, 3, 3, 4, 4, 3, 4, 3, 3, 3, 3, 3, 3, 4, 1, 3, 3, 4, 3, 4, 3, 3, 2, 3, 2]
    numWl = 30
    A= Type(H, Pg, K, numWl)
    print(A)
