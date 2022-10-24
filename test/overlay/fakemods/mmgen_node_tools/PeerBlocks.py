#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
fakemods.mmgen_node_tools.PeerBlocks: List blocks in flight, disconnect stalling nodes - test data
"""

from .PeerBlocks_orig import *

class fake_data:

	gp_counter = 0
	dn_counter = 0
	poll_secs = 0.5

	addresses = """
		0  3tokm3se4omuhhqgaxiam3yhl474ekbg5xb45kydfno57k7ooapitogv.onion:8333 /Satoshi:24.0.0/
		1  2rysrq5f2ec4zpnsohyb6mc6l6unosjwaydjefttt34ouogdpqtlo7a5.onion:8333 /Satoshi:0.21.1/
		2  5bkcnkrihwowji7zwko7ddtpcetz6572zbwdh6aguyt2yz3wgvzqa3ne.onion:8333 /Satoshi:23.0.0/
		3  ukzy7yvako4z6tvtocsm33yvdxwyx567ioqwfezzewlw2syawzkgrw64.onion:8333 /Satoshi:22.0.0/
		4  b3r3hhxiauujwj7afmji63forvnd7uhq7ov5x2n7w7hvrhutoq3lhul7.onion:8333 /Satoshi:24.0.0/
		5  ksownpb4zk4vuyfiowgyvz3kzc2djeiurnnh7pyal3if54n5wzup3afm.onion:8333 /Satoshi:22.0.0/
		6  xh6vhun75w5y2s2xze2n4rarnduqvwowwthhyiaefly3df2t4guwvjrl.onion:8333 /Satoshi:22.0.0/
		7  raqbaqcsoldmk7sn6fgoh5bicrlzjdoexz5b2z7jemxb2u6z62vpxto2.onion:8333 /Satoshi:23.0.0/
		8  5gu3m7jr4tog5tuyisek2fxl5erjgasrxzarnii6cpemmvqhate36hrg.onion:8333 /Satoshi:25.1.0(Aldebaran 3.2.1)/
		9  ayiyxqgckls4fmzrbbh35ppquhstzhm453xezvzmuoglhnibrxu5ebos.onion:8333 /Satoshi:22.0.0/
		10 3zmyku3xqrb4mebi2r6l65l5ovmf5yjou2zeywgz5g2ehiqbclppwy6t.onion:8333 /Satoshi:23.0.0/
		11 ljyfsi4wponyw52o5y75bn6oxktw7kiaes3vdtzf26scapei2ed6yw4m.onion:8333 /Satoshi:0.21.0/
		12 n5hsupofuhis2xfx7neahntqjl2l3jjp7ait6jsegrp4utj7573qgqsp.onion:8333 /Satoshi:22.0.0/
		13 klw3dgcuzr4etnkgw5ysnukfl46urhnqrlvjt53v544p32o7acakyps4.onion:8333 /Satoshi:23.0.0/
		14 icmdqoko4nnqp4aiamiqihbvqlumqrmidyb7n54jdif2uki3qkprwsvd.onion:8333 /Satoshi:24.1.0/
	"""

	# connected peers for each iteration
	iterations = """
		01 0 1 2 3 4 5 6 7 8
		02 0 1 2 3 4 5 6 7
		03 0 1 2 3 4 5 6 7 8
		04 0 2 3 4 5 6 7 8 9
		05 0 2 3 4 5 6 7 8 9
		06 0 2 3 4 5 6 7 8 9 10
		07 0 2 3 4 5 6 7 8 9 10
		08 0 2 3 4 5 6 7 8 9 10
		09 0 2 3 4 5 6 7 8 9 10
		10 0 2 3 4 5 6 7 8 9 10
		11 2 3 4 5 6 7 8 9 10
		12 2 3 4 5 6 7 8 9 10
		13 2 3 4 5 6 7 8 9 10
		14 2 3 4 5 6 7 8 9 10
		15 2 3 4 5 6 7 8 9 10 12
		16 2 3 4 5 6 7 8 9 10 12
		17 2 3 4 5 6 7 8 9 10 12
		18 2 3 4 5 6 7 8 9 10 12
		19 2 3 5 6 7 8 9 10 12
		20 2 3 5 6 7 8 9 10 12
		21 2 3 5 6 7 8 9 10 12
		22 2 3 5 6 7 8 9 10 12
	"""

	# blocks in flight for each iteration for each peer
	blocks = {
	'0': """
		01 6917 6918 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083
		02 6917 6918 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083
		03 6917 6918 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083
		04 6918 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083 6913
		05 6918 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083 6913
		06 6918 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083 6913
		07 6918 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083 6913
		08 6918 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083 6913
		09 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083 6913 7183
		10 6920 6937 6939 6942 6944 6946 6947 6950 6951 6953 6971 6976 6985 7083 6913 7183
	""",
	'1': """
		01 6906 6907 6908 6909 6910 6911 6913 6915 6919 6940 6948 6982 6988 7000 7023 7062
		02 6906 6907 6908 6909 6910 6911 6913 6915 6919 6940 6948 6982 6988 7000 7023 7062
		03 6908 6909 6910 6911 6913 6915 6919 6940 6948 6982 6988 7000 7023 7062 7088 7107
	""",
	'2': """
		01 6990 6994 6996 6997 6999 7017 7018 7019 7020 7021 7025 7059 7060 7061 7082 7084
		02 6990 6994 6996 6997 6999 7017 7018 7019 7020 7021 7025 7059 7060 7061 7082 7084
		03 6997 6999 7017 7018 7019 7020 7021 7025 7059 7060 7061 7082 7084 7085 7089 7108
		04 7018 7019 7020 7021 7025 7059 7060 7061 7082 7084 7085 7089 7108 7113 6909 7000
		05 7018 7019 7020 7021 7025 7059 7060 7061 7082 7084 7085 7089 7108 7113 6909 7000
		06 7020 7021 7025 7059 7060 7061 7082 7084 7085 7089 7108 7113 6909 7000 7112 7142
		07 7025 7059 7060 7061 7082 7084 7085 7089 7108 7113 6909 7000 7112 7142 7164 7173
		08 7059 7060 7061 7082 7084 7085 7089 7108 7113 6909 7000 7112 7142 7164 7173 7179
		09 7060 7061 7082 7084 7085 7089 7108 7113 6909 7000 7112 7142 7164 7173 7179 7190
		10 7061 7082 7084 7085 7089 7108 7113 6909 7000 7112 7142 7164 7173 7179 7190 7201
		11 7084 7085 7089 7108 7113 6909 7000 7112 7142 7164 7173 7179 7190 7201 7209 6942
		12 7085 7089 7108 7113 6909 7000 7112 7142 7164 7173 7179 7190 7201 7209 6942 6985
		13 7085 7089 7108 7113 6909 7000 7112 7142 7164 7173 7179 7190 7201 7209 6942 6985
		14 7089 7108 7113 6909 7000 7112 7142 7164 7173 7179 7190 7201 7209 6942 6985 7217
		15 7108 7113 6909 7000 7112 7142 7164 7173 7179 7190 7201 7209 6942 6985 7217 7245
		16 6909 7000 7112 7142 7164 7173 7179 7190 7201 7209 6942 6985 7217 7245 7250 7261
		17 6909 7000 7112 7142 7164 7173 7179 7190 7201 7209 6942 6985 7217 7245 7250 7261
		18 7173 7179 7190 7201 7209 6942 6985 7217 7245 7250 7261 7289 7314 7319 7325 7360
		19 7179 7190 7201 7209 6942 6985 7217 7245 7250 7261 7289 7314 7319 7325 7360 7379
		20 7190 7201 7209 6942 6985 7217 7245 7250 7261 7289 7314 7319 7325 7360 7379 7188
		21 7209 6942 6985 7217 7245 7250 7261 7289 7314 7319 7325 7360 7379 7188 7324 7388
		22 7209 6942 6985 7217 7245 7250 7261 7289 7314 7319 7325 7360 7379 7188 7324 7388
	""",
	'3': """
		01 6974 6977 6978 6979 6983 6986 6991 6992 6993 6995 6998 7022 7024 7058 7063 7081
		02 6974 6977 6978 6979 6983 6986 6991 6992 6993 6995 6998 7022 7024 7058 7063 7081
		03 6977 6978 6979 6983 6986 6991 6992 6993 6995 6998 7022 7024 7058 7063 7081 7106
		04 6979 6983 6986 6991 6992 6993 6995 6998 7022 7024 7058 7063 7081 7106 7119 6982
		05 6979 6983 6986 6991 6992 6993 6995 6998 7022 7024 7058 7063 7081 7106 7119 6982
		06 6986 6991 6992 6993 6995 6998 7022 7024 7058 7063 7081 7106 7119 6982 7136 7161
		07 6991 6992 6993 6995 6998 7022 7024 7058 7063 7081 7106 7119 6982 7136 7161 7170
		08 6992 6993 6995 6998 7022 7024 7058 7063 7081 7106 7119 6982 7136 7161 7170 7177
		09 6993 6995 6998 7022 7024 7058 7063 7081 7106 7119 6982 7136 7161 7170 7177 7186
		10 6995 6998 7022 7024 7058 7063 7081 7106 7119 6982 7136 7161 7170 7177 7186 7195
		11 7022 7024 7058 7063 7081 7106 7119 6982 7136 7161 7170 7177 7186 7195 6937 6946
		12 7022 7024 7058 7063 7081 7106 7119 6982 7136 7161 7170 7177 7186 7195 6937 6946
		13 7024 7058 7063 7081 7106 7119 6982 7136 7161 7170 7177 7186 7195 6937 6946 7214
		14 7058 7063 7081 7106 7119 6982 7136 7161 7170 7177 7186 7195 6937 6946 7214
		15 7058 7063 7081 7106 7119 6982 7136 7161 7170 7177 7186 7195 6937 6946 7214 7223
		16 7081 7106 7119 6982 7136 7161 7170 7177 7186 7195 6937 6946 7214 7223 7247 7257
		17 7106 7119 6982 7136 7161 7170 7177 7186 7195 6937 6946 7214 7223 7247 7257 7272
		18 7257 7272 7279 7287 7297 7300 7305 7318 7326 7332 7339 7341 7352 7359 7369 7373
		19 7279 7287 7297 7300 7305 7318 7326 7332 7339 7341 7352 7359 7369 7373 7381 7383
		20 7287 7297 7300 7305 7318 7326 7332 7339 7341 7352 7359 7369 7373 7381 7383 7259
		21 7297 7300 7305 7318 7326 7332 7339 7341 7352 7359 7369 7373 7381 7383 7259 7389
		22 7297 7300 7305 7318 7326 7332 7339 7341 7352 7359 7369 7373 7381 7383 7259 7389
	""",
	'4': """
		01 7002 7003 7004 7005 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080
		02 7002 7003 7004 7005 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080
		03 7003 7004 7005 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109
		04 7004 7005 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915
		05 7004 7005 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915
		06 7005 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160
		07 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172
		08 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172
		09 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188
		10 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188
		11 7008 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188 7205
		12 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188 7205 7083
		13 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188 7205 7083
		14 7009 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188 7205 7083
		15 7010 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188 7205 7083 7225
		16 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188 7205 7083 7225 7259
		17 7011 7012 7013 7014 7015 7016 7080 7109 6915 7160 7172 7188 7205 7083 7225 7259
		18 6915 7160 7172 7188 7205 7083 7225 7259 7278 7291 7317 7324 7345 7358 7364 7370
	""",
	'5': """
		01 7026 7027 7028 7029 7030 7031 7032 7033 7034 7035 7036 7037 7038 7039 7040 7041
		02 7026 7027 7028 7029 7030 7031 7032 7033 7034 7035 7036 7037 7038 7039 7040 7041
		03 7028 7029 7030 7031 7032 7033 7034 7035 7036 7037 7038 7039 7040 7041 7086 7110
		04 7031 7032 7033 7034 7035 7036 7037 7038 7039 7040 7041 7086 7110 7116 6910 7088
		05 7031 7032 7033 7034 7035 7036 7037 7038 7039 7040 7041 7086 7110 7116 6910 7088
		06 7032 7033 7034 7035 7036 7037 7038 7039 7040 7041 7086 7110 7116 6910 7088 7143
		07 7033 7034 7035 7036 7037 7038 7039 7040 7041 7086 7110 7116 6910 7088 7143 7167
		08 7034 7035 7036 7037 7038 7039 7040 7041 7086 7110 7116 6910 7088 7143 7167 7180
		09 7035 7036 7037 7038 7039 7040 7041 7086 7110 7116 6910 7088 7143 7167 7180 7185
		10 7037 7038 7039 7040 7041 7086 7110 7116 6910 7088 7143 7167 7180 7185 7194 7200
		11 7041 7086 7110 7116 6910 7088 7143 7167 7180 7185 7194 7200 7206 7207 6939 6944
		12 7116 6910 7088 7143 7167 7180 7185 7194 7200 7206 7207 6939 6944 6950 6951 6953
		13 6910 7088 7143 7167 7180 7185 7194 7200 7206 7207 6939 6944 6950 6951 6953 7211
		14 7088 7143 7167 7180 7185 7194 7200 7206 7207 6939 6944 6950 6951 6953 7211 7220
		15 7143 7167 7180 7185 7194 7200 7206 7207 6939 6944 6950 6951 6953 7211 7220 7224
		16 7180 7185 7194 7200 7206 7207 6939 6944 6950 6951 6953 7211 7220 7224 7246 7263
		17 7185 7194 7200 7206 7207 6939 6944 6950 6951 6953 7211 7220 7224 7246 7263 7268
		18 7220 7224 7246 7263 7268 7275 7283 7296 7308 7321 7330 7335 7336 7349 7353 7371
		19 7224 7246 7263 7268 7275 7283 7296 7308 7321 7330 7335 7336 7349 7353 7371 6915
		20 7224 7246 7263 7268 7275 7283 7296 7308 7321 7330 7335 7336 7349 7353 7371 6915
		21 7268 7275 7283 7296 7308 7321 7330 7335 7336 7349 7353 7371 6915 7385 7391 7392
		22 7283 7296 7308 7321 7330 7335 7336 7349 7353 7371 6915 7385 7391 7392 7400 7408
	""",
	'6': """
		01 7042 7043 7044 7045 7046 7047 7048 7049 7050 7051 7052 7053 7054 7055 7056 7057
		02 7043 7044 7045 7046 7047 7048 7049 7050 7051 7052 7053 7054 7055 7056 7057
		03 7045 7046 7047 7048 7049 7050 7051 7052 7053 7054 7055 7056 7057 7087
		04 7048 7049 7050 7051 7052 7053 7054 7055 7056 7057 7087 7115 6940
		05 7049 7050 7051 7052 7053 7054 7055 7056 7057 7087 7115 6940
		06 7051 7052 7053 7054 7055 7056 7057 7087 7115 6940 7141
		07 7052 7053 7054 7055 7056 7057 7087 7115 6940 7141
		08 7054 7055 7056 7057 7087 7115 6940 7141 7176
		09 7055 7056 7057 7087 7115 6940 7141 7176
		10 7056 7057 7087 7115 6940 7141 7176
		11 7057 7087 7115 6940 7141 7176
		12 7087 7115 6940 7141 7176
		13 6940 7141 7176 7213
		14 7141 7176 7213
		15 7141 7176 7213
		16 7141 7176 7213
		17 7141 7176 7213
		18 7141 7176 7213
		19 7176 7213
		20 7176 7213
		21 7213
		22
	""",
	'7': """
		01 7064 7065 7066 7067 7068 7069 7070 7071 7072 7073 7074 7075 7076 7077 7078 7079
		02 7064 7065 7066 7067 7068 7069 7070 7071 7072 7073 7074 7075 7076 7077 7078 7079
		03 7064 7065 7066 7067 7068 7069 7070 7071 7072 7073 7074 7075 7076 7077 7078 7079
		04 7067 7068 7069 7070 7071 7072 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988
		05 7067 7068 7069 7070 7071 7072 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988
		06 7068 7069 7070 7071 7072 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988 7139
		07 7069 7070 7071 7072 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988 7139 7166
		08 7070 7071 7072 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988 7139 7166 7175
		09 7071 7072 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988 7139 7166 7175 7187
		10 7072 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988 7139 7166 7175 7187 7198
		11 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988 7139 7166 7175 7187 7198 6913
		12 7073 7074 7075 7076 7077 7078 7079 7111 7118 6988 7139 7166 7175 7187 7198 6913
		13 7075 7076 7077 7078 7079 7111 7118 6988 7139 7166 7175 7187 7198 6913 7210 7212
		14 7075 7076 7077 7078 7079 7111 7118 6988 7139 7166 7175 7187 7198 6913 7210 7212
		15 7076 7077 7078 7079 7111 7118 6988 7139 7166 7175 7187 7198 6913 7210 7212 7226
		16 7078 7079 7111 7118 6988 7139 7166 7175 7187 7198 6913 7210 7212 7226 7254 7265
		17 7078 7079 7111 7118 6988 7139 7166 7175 7187 7198 6913 7210 7212 7226 7254 7265
		18 6913 7210 7212 7226 7254 7265 7276 7284 7285 7293 7304 7306 7323 7333 7346 7355
		19 7212 7226 7254 7265 7276 7284 7285 7293 7304 7306 7323 7333 7346 7355 7375 7083
		20 7212 7226 7254 7265 7276 7284 7285 7293 7304 7306 7323 7333 7346 7355 7375 7083
		21 7254 7265 7276 7284 7285 7293 7304 7306 7323 7333 7346 7355 7375 7083 7345 7395
		22 7276 7284 7285 7293 7304 7306 7323 7333 7346 7355 7375 7083 7345 7395 7396 7405
	""",
	'8': """
		03 7090 7091 7092 7093 7094 7095 7096 7097 7098 7099 7100 7101 7102 7103 7104 7105
		04 7095 7096 7097 7098 7099 7100 7101 7102 7103 7104 7105 7114 7117 6911 6948 7023
		05 7095 7096 7097 7098 7099 7100 7101 7102 7103 7104 7105 7114 7117 6911 6948 7023
		06 7097 7098 7099 7100 7101 7102 7103 7104 7105 7114 7117 6911 6948 7023 7137 7140
		07 7099 7100 7101 7102 7103 7104 7105 7114 7117 6911 6948 7023 7137 7140 7162 7169
		08 7100 7101 7102 7103 7104 7105 7114 7117 6911 6948 7023 7137 7140 7162 7169 7178
		09 7103 7104 7105 7114 7117 6911 6948 7023 7137 7140 7162 7169 7178 7182 7189 7191
		10 7105 7114 7117 6911 6948 7023 7137 7140 7162 7169 7178 7182 7189 7191 7193 7199
		11 7114 7117 6911 6948 7023 7137 7140 7162 7169 7178 7182 7189 7191 7193 7199 6920
		12 7117 6911 6948 7023 7137 7140 7162 7169 7178 7182 7189 7191 7193 7199 6920 6971
		13 7117 6911 6948 7023 7137 7140 7162 7169 7178 7182 7189 7191 7193 7199 6920 6971
		14 6911 6948 7023 7137 7140 7162 7169 7178 7182 7189 7191 7193 7199 6920 6971 7222
		15 6911 6948 7023 7137 7140 7162 7169 7178 7182 7189 7191 7193 7199 6920 6971 7222
		16 7162 7169 7178 7182 7189 7191 7193 7199 6920 6971 7222 7248 7249 7256 7260 7264
		17 7169 7178 7182 7189 7191 7193 7199 6920 6971 7222 7248 7249 7256 7260 7264 7270
		18 7199 6920 6971 7222 7248 7249 7256 7260 7264 7270 7280 7290 7309 7329 7348 7366
		19 6971 7222 7248 7249 7256 7260 7264 7270 7280 7290 7309 7329 7348 7366 7380 7172
		20 6971 7222 7248 7249 7256 7260 7264 7270 7280 7290 7309 7329 7348 7366 7380 7172
		21 7248 7249 7256 7260 7264 7270 7280 7290 7309 7329 7348 7366 7380 7172 7291 7387
		22 7260 7264 7270 7280 7290 7309 7329 7348 7366 7380 7172 7291 7387 7399 7402 7406
	""",
	'9': """
		04 7122 7123 7124 7125 7126 7127 7128 7129 7130 7131 7132 7133 7134 7135 6919 7062
		05 7123 7124 7125 7126 7127 7128 7129 7130 7131 7132 7133 7134 7135 6919 7062 7107
		06 7124 7125 7126 7127 7128 7129 7130 7131 7132 7133 7134 7135 6919 7062 7107 7138
		07 7125 7126 7127 7128 7129 7130 7131 7132 7133 7134 7135 6919 7062 7107 7138 7168
		08 7126 7127 7128 7129 7130 7131 7132 7133 7134 7135 6919 7062 7107 7138 7168 7181
		09 7127 7128 7129 7130 7131 7132 7133 7134 7135 6919 7062 7107 7138 7168 7181 7184
		10 7131 7132 7133 7134 7135 6919 7062 7107 7138 7168 7181 7184 7196 7197 7202 7204
		11 7132 7133 7134 7135 6919 7062 7107 7138 7168 7181 7184 7196 7197 7202 7204 7208
		12 7134 7135 6919 7062 7107 7138 7168 7181 7184 7196 7197 7202 7204 7208 6947 6976
		13 7135 6919 7062 7107 7138 7168 7181 7184 7196 7197 7202 7204 7208 6947 6976 7215
		14 6919 7062 7107 7138 7168 7181 7184 7196 7197 7202 7204 7208 6947 6976 7215 7219
		15 7062 7107 7138 7168 7181 7184 7196 7197 7202 7204 7208 6947 6976 7215 7219 7244
		16 7138 7168 7181 7184 7196 7197 7202 7204 7208 6947 6976 7215 7219 7244 7252 7262
		17 7168 7181 7184 7196 7197 7202 7204 7208 6947 6976 7215 7219 7244 7252 7262 7269
		18 7215 7219 7244 7252 7262 7269 7286 7301 7313 7328 7337 7340 7351 7362 7367 7372
		19 7244 7252 7262 7269 7286 7301 7313 7328 7337 7340 7351 7362 7367 7372 7382 7160
		20 7252 7262 7269 7286 7301 7313 7328 7337 7340 7351 7362 7367 7372 7382 7160 7205
		21 7301 7313 7328 7337 7340 7351 7362 7367 7372 7382 7160 7205 7278 7370 7390 7393
		22 7337 7340 7351 7362 7367 7372 7382 7160 7205 7278 7370 7390 7393 7397 7404 7407
	""",
	'10': """
		06 7144 7145 7146 7147 7148 7149 7150 7151 7152 7153 7154 7155 7156 7157 7158 7159
		07 7147 7148 7149 7150 7151 7152 7153 7154 7155 7156 7157 7158 7159 7163 7165 7171
		08 7148 7149 7150 7151 7152 7153 7154 7155 7156 7157 7158 7159 7163 7165 7171 7174
		09 7149 7150 7151 7152 7153 7154 7155 7156 7157 7158 7159 7163 7165 7171 7174 7192
		10 7150 7151 7152 7153 7154 7155 7156 7157 7158 7159 7163 7165 7171 7174 7192 7203
		11 7150 7151 7152 7153 7154 7155 7156 7157 7158 7159 7163 7165 7171 7174 7192 7203
		12 7151 7152 7153 7154 7155 7156 7157 7158 7159 7163 7165 7171 7174 7192 7203 7183
		13 7152 7153 7154 7155 7156 7157 7158 7159 7163 7165 7171 7174 7192 7203 7183 7216
		14 7154 7155 7156 7157 7158 7159 7163 7165 7171 7174 7192 7203 7183 7216 7218 7221
		15 7155 7156 7157 7158 7159 7163 7165 7171 7174 7192 7203 7183 7216 7218 7221 7227
		16 7158 7159 7163 7165 7171 7174 7192 7203 7183 7216 7218 7221 7227 7251 7258 7267
		17 7159 7163 7165 7171 7174 7192 7203 7183 7216 7218 7221 7227 7251 7258 7267 7273
		18 7277 7282 7288 7294 7302 7312 7320 7327 7331 7338 7347 7354 7357 7361 7365 7368
		19 7288 7294 7302 7312 7320 7327 7331 7338 7347 7354 7357 7361 7365 7368 7376 7378
		20 7288 7294 7302 7312 7320 7327 7331 7338 7347 7354 7357 7361 7365 7368 7376 7378
		21 7302 7312 7320 7327 7331 7338 7347 7354 7357 7361 7365 7368 7376 7378 7364 7394
		22 7327 7331 7338 7347 7354 7357 7361 7365 7368 7376 7378 7364 7394 7401 7403 7410
	""",
	'12': """
		15 7228 7229 7230 7231 7232 7233 7234 7235 7236 7237 7238 7239 7240 7241 7242 7243
		16 7230 7231 7232 7233 7234 7235 7236 7237 7238 7239 7240 7241 7242 7243 7253 7266
		17 7231 7232 7233 7234 7235 7236 7237 7238 7239 7240 7241 7242 7243 7253 7266 7274
		18 7281 7292 7298 7299 7303 7307 7310 7311 7316 7322 7334 7343 7344 7350 7356 7363
		19 7299 7303 7307 7310 7311 7316 7322 7334 7343 7344 7350 7356 7363 7374 7377 7384
		20 7303 7307 7310 7311 7316 7322 7334 7343 7344 7350 7356 7363 7374 7377 7384 7225
		21 7310 7311 7316 7322 7334 7343 7344 7350 7356 7363 7374 7377 7384 7225 7317 7386
		22 7316 7322 7334 7343 7344 7350 7356 7363 7374 7377 7384 7225 7317 7386 7398 7409
	"""
	}

	def make_address_data():
		for line in fake_data.addresses.strip().split('\n'):
			data = line.split(maxsplit=2)
			yield (data[0], {k:v for k,v in zip(('id','addr','subver'),data)})

	def make_iterations_data():
		for line in fake_data.iterations.strip().split('\n'):
			data = line.split(maxsplit=1)
			yield (data[0], data[1].split())

	def make_blocks_data(iterations):
		for peer,blocks_str in fake_data.blocks.items():
			iter_strs = dict([s.lstrip().split(maxsplit=1) for s in blocks_str.strip().split('\n') if ' ' in s])
			yield (peer,dict((i,iter_strs.get(i,'').split()) for i in iterations))

	def make_data():
		address_data = dict(fake_data.make_address_data())
		iterations_data = dict(fake_data.make_iterations_data())
		blocks_data = dict(fake_data.make_blocks_data(iterations_data))

		def make_peerinfo(peer_id,blocks,iter_no):
			d = address_data[peer_id]
			return {
				'id': int(d['id']),
				'addr': d['addr'],
				'subver': d['subver'],
				'inflight': [int(n)+830000 for n in blocks[iter_no]],
			}

		def gen_data():
			for iter_no in iterations_data:
				yield (
					iter_no,
					[make_peerinfo(peer_id,blocks,iter_no) for peer_id,blocks in blocks_data.items()
						if peer_id in iterations_data[iter_no] ]
				)

		fake_data.peerinfo = dict(gen_data())

	async def get_info(self,rpc):
		fake_data.gp_counter = (fake_data.gp_counter % 22) + 1
		return fake_data.peerinfo[f'{fake_data.gp_counter:02d}']

	async def disconnect_node(self,rpc,addr):
		from mmgen.exception import RPCFailure
		fake_data.dn_counter += 1
		if fake_data.dn_counter % 2:
			raise RPCFailure
		else:
			pass

fake_data.make_data()

Display.poll_secs = fake_data.poll_secs
Display.get_info = fake_data.get_info
Display.disconnect_node = fake_data.disconnect_node
