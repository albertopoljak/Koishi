# -*- coding: utf-8 -*-
#each added move is from 3 elements for a total of 24 bits:
# x coordinate 1st 8 bit
# y coordinate middle 8 bit
# what u can do there last 8 bit
#   0b00000001 <- can move
#   0b00000010 <- could move
#   0b00000100 <- can hit
#   0b00001000 <- could hit
#   0b00010000 <- can special
#   0b00100000 <- could special

class Puppet_meta(object):
    __slots__=['generate_moves', 'name', 'piercees']
    def __init__(self,name,generate_moves,piercees):
        self.name=name
        self.generate_moves=generate_moves
        self.pierces=pierces
        setattr(type(self),name,self)

def rook_moves(self,field):
    position=self.position
    y,x=divmod(position,8)
    moves=self.moves

    for dim_i,v_diff,pos_diff,v_limit in (
            (0,-1,-1,0),
            (1,-1,-8,0),
            (0,+1,+1,7),
            (1,+1,+8,7),
                ):

        local_pos=position
        if dim_i:
            local_v=y
        else:
            local_v=x
        while True:
            if local_v==v_limit:
                break
            local_v+=v_diff
            local_pos+=pos_diff
            other=field[local_pos]
            if other is None:
                can_do=0b00001011 #free
            elif self.side==other.side:
                can_do=0b00001010 #could hit
            else:
                can_do=0b00001111 #hit
                
            if dim_i:
                moves.append((x<<16)|(local_v<<8)|can_do) 
            else:
                moves.append((local_v<<16)|(y<<8)|can_do)

            if can_do!=0b00001011:
                break

    #TODO: add castling

def rook_pierce(self,target,field):
    position=self.position
    y,x=divmod(position,8)

    other_y,other_x=divmod(target.position,8)
    if y!=other_y:
        dim_i=1
        if y>other_y:
            v_limit = 7
            v_diff  = 1
            pos_diff= 8
        else:
            v_limit = 0
            v_diff  =-1
            pos_diff=-8
        local_v=y+pos_diff
    else:
        dim_i=0
        if x>other_x:
            v_limit = 7
            v_diff  = 1
            pos_diff= 1
        else:
            v_limit = 0
            v_diff  =-1
            pos_diff=-1
        local_v=x+pos_diff

    moves=[]
    local_pos=position+pos_diff
    
    found=False
    while True:
        other=field[local_pos]
        if other is None:
            if dim_i:
                moves.append((x<<16)|(local_v<<8)) 
            else:
                moves.append((local_v<<16)|(y<<8))
        else:
            if not found:
                found=True
                continue

            if other.meta is Puppet_meta.king:
                return moves
            return
        
        if local_v==v_limit:
            return
        local_v+=v_diff
        local_pos+=pos_diff


        
def knight_move(self,field):
    position=self.position
    y,x=divmod(position,8)
    moves=self.moves

    for x_diff,y_diff,pos_diff in (
            (-1,-2,-17),
            (+1,-2,-15),
            (+2,-1, -6),
            (+2,+1,+10),
            (+1,+2,+17),
            (-1,+2,+15),
            (-2,+1, +6),
            (-2,-1,-10),
                ):

        local_x=x+x_diff
        local_y=y+y_diff
        if local_x<0 or local_x>7 or local_y<0 or local_y>7:
            continue

        other=field[position+pos_diff]
        if other is None:
            can_do=0b00001011 #free
        elif self.side==other.side:
            can_do=0b00001010 #could hit
        else:
            other.killers.append(self)
            can_do=0b00001111 #hit
        moves.append((local_x<<16)|(local_y<<8)|can_do) 

        if can_do!=0b00001011:
            break

def bishop_move(self,field):
    position=self.position
    y,x=divmod(position,8)
    moves=self.moves

    for x_diff,y_diff,pos_diff,x_limit,y_limit in (
            (-1,-1,-9,0,0),
            (+1,-1,-7,7,0),
            (+1,+1,+9,7,7),
            (-1,+1,+7,0,7),
                ):
        local_x=x
        local_y=y
        local_pos=position

        while True:
            if local_x==x_limit or local_y==y_limit:
                break
            local_x+=x_diff
            local_y+=y_diff
            local_pos+=pos_diff

            other=field[local_pos]
            if other is None:
                can_do=0b00001011 #free
            elif self.side==other.side:
                can_do=0b00001010 #could hit
            else:
                other.killers.append(self)
                can_do=0b00001111 #hit
                
            moves.append((local_x<<16)|(local_y<<8)|can_do)

            if can_do!=0b00001011:
                break

def queen_move(self,field):
    position=self.position
    y,x=divmod(position,8)
    moves=self.moves

    for x_diff,y_diff,pos_diff,x_limit,y_limit in (
            (-1,-1,-9,0,0),
            ( 0,-1,-8,8,0),
            (+1,-1,-7,7,0),
            (+1, 0,+1,7,8),
            (+1,+1,+9,7,7),
            ( 0,+1,+8,8,7),
            (-1,+1,+7,0,7),
            (-1, 0,-1,0,8),
                ):
        
        local_x=x
        local_y=y
        local_pos=position
        while True:
            if local_x==x_limit or local_y==y_limit:
                break
            local_x+=x_diff
            local_y+=y_diff
            local_pos+=pos_diff

            other=field[local_pos]
            if other is None:
                can_do=0b00001011 #free
            elif self.side==other.side:
                can_do=0b00001010 #could hit
            else:
                other.killers.append(self)
                can_do=0b00001111 #hit
            moves.append((local_x<<16)|(local_y<<8)|can_do)

            if can_do!=0b00001011:
                break
            break

def king_move(self,field):
    position=self.position
    y,x=divmod(position,8)
    moves=self.moves

    for x_diff,y_diff,pos_diff,x_limit,y_limit in (
            (-1,-1,-9,0,0),
            ( 0,-1,-8,8,0),
            (+1,-1,-7,7,0),
            (+1, 0,+1,7,8),
            (+1,+1,+9,7,7),
            ( 0,+1,+8,8,7),
            (-1,+1,+7,0,7),
            (-1, 0,-1,0,8),
                ):
        
        if x==x_limit or y==y_limit:
            continue
        
        local_x=x+x_diff
        local_y=y+y_diff
        local_pos=position+pos_diff

        other=field[local_pos]
        if other is None:
            can_do=0b00001011 #free
        elif self.side==other.side:
            can_do=0b00001010 #could hit
        else:
            other.killers.append(self)
            can_do=0b00001111 #hit
        
        moves.append((local_x<<16)|(local_y<<8)|can_do)

    #TODO : add castling

def pawn_moves(self,field):
    position=self.position
    y,x=divmod(position,8)
    moves=self.moves

    if self.side:
        other=field[position+8]
        if y==6:
            can_do=0b00110011 if other is None else 0b00100010
            moves.append((x<<16)|(7<<8)|can_do) #evolve

            if x>0:
                other=field[position+7]
                if other is None or self.side==other.side:
                    can_do=0b00101000 #could hit
                else:
                    moves.killers.append(self)
                    can_do=0b00111101 #hit
                moves.append(((x-1)<<16)|(7<<8)|can_do)
                    
            if x<7:
                other=field[position+9]
                if other is None or self.side==other.side:
                    can_do=0b00101000 #could hit
                else:
                    other.killers.append(self)
                    can_do=0b00111101 #hit
                moves.append(((x+1)<<16)|((y+1)<<8)|can_do)
        else:
            can_do=0b00000011 if other is None else 0b00000010
            moves.append((x<<16)|((y+1)<<8)|can_do) #general forward
            if other is None and not self.moved and y<2:
                other=field[position+16]
                can_do=0b00000011 if other is None else 0b00000010
                moves.append((x<<16)|((y+2)<<8)|can_do) #double on default position

            if x>0:
                other=field[position+7]
                if other is None or self.side==other.side:
                    can_do=0b00001000 #could hit
                else:
                    moves.killers.append(self)
                    can_do=0b00001101 #hit
                moves.append(((x-1)<<16)|((y+1)<<8)|can_do)
                    
            if x<7:
                other=field[position+9]
                if other is None or self.side==other.side:
                    can_do=0b00001000 #could hit
                else:
                    other.killers.append(self)
                    can_do=0b00001101 #can hit
                moves.append(((x+1)<<16)|((y+1)<<8)|can_do)
    else:
        other=field[position-8]
        if y==1:
            can_do=0b00110011 if other is None else 0b00100010
            moves.append((x<<8)|can_do) #evolve

            if x>0:
                other=field[position-9]
                if other is None or self.side==other.side:
                    can_do=0b00101000 #could hit
                else:
                    other.killers.append(self)
                    can_do=0b00111101 #hit
                moves.append(((x-1)<<16)|can_do) #hit
                
            if x<7:
                other=field[position-7]
                if other is None or self.side==other.side:
                    can_do=0b00001000 #could hit
                else:
                    other.killers.append(self)
                    can_do=0b00001101 #hit
                moves.append(((x+1)<<16)|((y-1)<<8)|can_do)
                    
        else:
            can_do=0b00000011 if other is None else 0b00000010
            moves.append((x<<16)|((y-1)<<8)|can_do) #general forward
            if other is None and not self.moved and y>5:
                other=field[position-16]
                can_do=0b00000011 if other is None else 0b00000010
                moves.append((x<<16)|((y-2)<<8)|can_do) #double on default position
                
            if x>0:
                other=field[position-9]
                if other is None or self.side==other.side:
                    can_do=0b00001000 #could hit
                else:
                    other.killers.append(self)
                    can_do=0b00001101 #hit
                moves.append(((x-1)<<16)|((y-1)<<8)|can_do) 
            
            if x<7:
                other=field[position-7]
                if other is None or self.side==other.side:
                    can_do=0b00001000 #could hit
                else:
                    other.killers.append(self)
                    can_do=0b00001101 #hit
                moves.append(((x+1)<<16)|((y-1)<<8)|can_do) #hit

def check_king_moves(puppet,player,others):
    moves=puppet.moves
    for index in reversed(range(len(moves))):
        element=moves[index]
        if element&0b00000001:
            binary_pos=element&0xffff00
            
            other_index=0
            other_limit=len(others)
            other_moves=others[0].moves
            move_index=0
            move_limit=len(other_moves)
            
            while True:
                if move_index<move_limit:
                    move=other_moves[move_index]
                    if move&0xffff00==binary_pos and move&0b00001000:
                        del moves[index]
                        break
                    move_index=move_index+1
                    continue

                other_index=other_index+1
                if other_index==other_limit:
                    break
                other_moves=others[other_index].moves
                move_index=0
                move_limit=len(other_moves)

    #TODO: calculate blocking moves to defend the king
            

Puppet_meta('rook',     rook_moves,     True)
Puppet_meta('knight',   knight_moves,   False)
Puppet_meta('bishop',   bishop_moves,   True)
Puppet_meta('queen',    queen_moves,    True)
Puppet_meta('king',     king_moves,     False)
Puppet_meta('pawn',     pawn_moves,     False)

del rook_moves
del knight_moves
del bishop_moves
del queen_moves
del king_moves
del pawn_moves

class Puppet(object):
    __slots__=['effects', 'meta', 'moved', 'position', 'side','moves','killers']
    def __init__(self,meta,position,side):
        self.meta       = meta
        self.position   = position
        self.side       = side
        self.effects    = []
        self.moved      = 0 #needs for special checks
        self.moves      = []
        self.killers    = []

    def update(self,field):
        for effect in self.effects:
            effect.apply(self)

        self.moves.clear()
        self.killers.clear()
        
        self.meta.generate_moves(self,field)

    def __repr__(self):
        return f'<{("light","dark")[self.side]} {self.meta.name} effetcts=[{", ".join([repr(effect) for effect in self.effects])}]>'

class chesuto_backend(object):
    __slots__=['field','players']
    def __init__(self,player_0,player_1):
        self.field=[
            Puppet(Puppet_meta.rook,    0,  1),
            Puppet(Puppet_meta.knight,  1,  1),
            Puppet(Puppet_meta.bishop,  2,  1),
            Puppet(Puppet_meta.queen,   3,  1),
            Puppet(Puppet_meta.king,    4,  1),
            Puppet(Puppet_meta.bishop,  5,  1),
            Puppet(Puppet_meta.knight,  6,  1),
            Puppet(Puppet_meta.rook,    7,  1),
            *(Puppet(Puppet_meta.pawn,  pos,1) for pos in range(8,16)),
            *(None for _ in range(16,48)),
            *(Puppet(Puppet_meta.pawn,  pos,0) for pos in range(48,56)),
            Puppet(Puppet_meta.rook,    56, 0),
            Puppet(Puppet_meta.knight,  57, 0),
            Puppet(Puppet_meta.bishop,  58, 0),
            Puppet(Puppet_meta.queen,   59, 0),
            Puppet(Puppet_meta.king,    60, 0),
            Puppet(Puppet_meta.bishop,  61, 0),
            Puppet(Puppet_meta.knight,  62, 0),
            Puppet(Puppet_meta.rook,    63, 0),
                ]

        self.players=(player_0(self,0),player_1(self,1))

        def check(self,player,x,y):
            puppet=self.field[x+(y<<3)]
            if puppet is not None:
                return puppet.moves,puppet.killers

            binary_pos=(x<<16)+(y<<8)
            moves=[]
            killers=[]
            
            player2=self.players[player.side^1]
            
            for puppet_ in player.puppets:
                for move in puppet.moves:
                    if move&0xffff00==binary_pos and move&0b00000001:
                        position=puppet.position
                        moves.append(((position&0b00000111)<<16)|((position&0b00111000)<<5)|0b00000001)
            for puppet_ in player2.puppets:
                for move in puppet.moves:
                    if move&0xffff00==binary_pos and move&0b00001000:
                        killers.append(puppet)

            return moves,killers
            
    def update_puppets(self):
        field=self.field
        players=self.players
        for player in players:
            for puppet in player.puppets:
                puppet.update(field)

    def __repr__(self):
        result=[]
        
        line=['|---' for _ in range(8)]
        line.append('|\n')
        line_breaker=''.join(line)
        line.clear()
        
        field=self.field
        for y in range(0,64,8):
            result.append(line_breaker)
            
            for pos in range(y,y+8):
                line.append('|')
                puppet=field[pos]
                if puppet is None:
                    line.append('   ')
                else:
                    line.append(f'{("L","D")[puppet.side]}{puppet.meta.name[:2]}')
            line.append('|\n')
            
            result.append(''.join(line))
            line.clear()

        result.append(line_breaker)
        return ''.join(result)
    
class chesuto_player(object):
    __slots__=['backend', 'channel', 'puppets', 'side', 'user','king','in_check']
    def __init__(self,user,channel):
        self.user=user
        self.channel=channel
        self.in_check=False
        
    def __call__(self,backend,side):
        self.backend=backend
        self.side=side
        
        if side:
            self.king   =backend.field[4]
            self.puppets=backend.field[:16]
        else:
            self.king   =backend.field[60]
            self.puppets=backend.field[48:]
        return self
            


