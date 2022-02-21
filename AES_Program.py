
from distutils.log import error

class AES_Program:
    blockLength : int = 128 # how many bits AES processes at once
    bitsPerByte : int = 8 # how many bits are used to encode a char
    bytesPerBlock = blockLength // bitsPerByte # how many bytes are in a block
    encoding = 'utf-8' # encoding used for strings

    def EncryptAES_ECB(self, message, key):
        # message should be a string of characters
        # cut message into blockLength long blocks
        messageBlocks = self.MessageToMessageBlocks(message)
        # encrypt blocks in series
        cipher = AES()
        cryptogramBlocks = [cipher.AESEncrypt(messageBlocks[i], key) for i in range(0, len(messageBlocks))]
        # concatenate blocks into a single byte array
        cryptogram = self.CryptogramBlocksToCryptogram(cryptogramBlocks)
        return cryptogram

    def DecryptAES_ECB(self, cryptogram, key):
        # cut cryptogram into blockLength long blocks
        cryptogramBlocks = self.CryptogramToCryptogramBlocks(cryptogram)
        # decrypt blocks in parallel
        decipher = AES()
        messageBlocks = [decipher.AESDecrypt(cryptogramBlocks[i], key) for i in range(0, len(cryptogramBlocks))]
        # convert byte blocks to character blocks
        message = self.MessageBlocksToMessage(messageBlocks)
        return message    

    def EncryptAES_CBC(self, message, key, IV):   
        # message should be a string of characters
        # cut message into blockLength long blocks
        messageBlocks = self.MessageToMessageBlocks(message)
        # encrypt blocks in series
        cipher = AES()
        cryptogramBlocks = []
        previousCryptogramBits = IV # IV is used as the first "latest cryptogram block"
        for i in range(0, len(messageBlocks)):
            # encrypt the result of XORing message block with latest cryptogram block
            cryptogramBlocks = cryptogramBlocks + [cipher.AESEncrypt(sxor(previousCryptogramBits, messageBlocks[i]), key)]
            previousCryptogramBits = cryptogramBlocks[i]

        # concatenate blocks into a single stream
        cryptogram = self.CryptogramBlocksToCryptogram(cryptogramBlocks)
        return cryptogram

    def DecryptAES_CBC(self, cryptogram, key, IV):
        # cut cryptogram into blockLength long blocks
        cryptogramBlocks = self.CryptogramToCryptogramBlocks(cryptogram)
        # decrypt blocks in parallel
        decipher = AES()
        messageBlocks = []
        previousCryptogramBlock = IV # IV is used as the first "latest cryptogram block"
        for i in range(0, len(cryptogramBlocks)):
            # encrypt the result of XORing message block with latest cryptogram block
            messageBlocks = messageBlocks + [sxor(previousCryptogramBlock, decipher.AESDecrypt(cryptogramBlocks[i], key))]
            previousCryptogramBlock = cryptogramBlocks[i]
        
        # convert byte blocks to character blocks
        message = self.MessageBlocksToMessage(messageBlocks)
        return message  

    def MessageToMessageBlocks(self, message):
        # convert string to bytes
        stringBytes = bytearray(message, self.encoding)
        # split into 16 byte long blocks
        byteBlocks = [stringBytes[i:i + self.bytesPerBlock] for i in range(0, len(stringBytes), self.bytesPerBlock)]
        # make sure last block is of correct length (perform PKCS#7 padding)
        lastBlockLength = len(byteBlocks[-1])
        if(lastBlockLength < self.bytesPerBlock):
            byteBlocks[-1] = byteBlocks[-1].ljust(self.bytesPerBlock) # extend last block to be of correct length
        else:
            # the message length is a multiple of block size: add whole padding block
            paddingBlock = bytearray(self.bytesPerBlock)
            byteBlocks.append(paddingBlock)
            lastBlockLength = 0 # make sure we will be setting byte values to full block length       
        # set values of padding bytes
        for i in range(lastBlockLength, self.bytesPerBlock):
            byteBlocks[-1][i] = self.bytesPerBlock - lastBlockLength

        return byteBlocks

    def MessageBlocksToMessage(self, byteBlocks : list[bytearray]):
        # concatenate bytes into a single block
        bytes = bytearray(b'')
        for i in range(0, len(byteBlocks)):
            bytes += byteBlocks[i]
        # remove padding (revert PKCS#7 padding)
        paddingBytes = bytes[-1]
        bytes = bytes[:-paddingBytes]
        # convert to string
        string = bytes.decode(self.encoding, 'ignore')
        return string

    def CryptogramBlocksToCryptogram(self, cryptogramBlocks):
        cryptogram = b''
         # concatenate bytes into a single block
        for i in range(0,len(cryptogramBlocks)):
            cryptogram = cryptogram + cryptogramBlocks[i]
        return cryptogram

    def CryptogramToCryptogramBlocks(self, cryptogram):
        # split into 16 byte long blocks
        byteBlocks = [cryptogram[i:i + self.bytesPerBlock] for i in range(0, len(cryptogram), self.bytesPerBlock)]
        return byteBlocks


    def Tests(self):
        allowedKeyLengths = [16, 24, 32]

        errorCount = 0
        print("Hello, this is our AES implementation in python:")
        for test in self.tests:
            keyString = self.tests[test]['key']
            key = bytearray(keyString, self.encoding)

            keyLength = len(key)
            if(keyLength not in allowedKeyLengths):
                error("Error: Incorrect test detected:\n Key of unsupported length for test: {}\n please fix and run tests again".format(test))
                return
            key = key.ljust(keyLength, b'\0')
            mode = self.tests[test]['mode']
            message = self.tests[test]['message']
            print("\nEncrypting the following message in {} mode, (key :{}):".format(mode, key))
            print(message)
            if mode == "ECB":
                # use ECB mode 
                print("Result:")
                cryptogram = self.EncryptAES_ECB(message, key)
                expectedCryptogram = self.tests[test]['expectedCryptogram']         
                errorCount += self.TestAndAnnounce(cryptogram.hex(), expectedCryptogram)
                print('Decrypting...')
                decryptedMessage = self.DecryptAES_ECB(cryptogram, key)
                print('Decrypted message:')
                errorCount += self.TestAndAnnounce(decryptedMessage, message)
            elif mode == "CBC":
                
                if(self.tests[test]['initialValue'] == None or len(self.tests[test]['initialValue']) != self.bytesPerBlock) :
                    error("Error: Incorrect test detected:\n Invalid initialValue for CBC test: {}\n please fix and run tests again".format(test))
                    return
                # use CBC mode
                iv = bytearray(self.tests[test]['initialValue'], self.encoding)
                print('Using Initial Variable: {}'.format(iv))        
                print("Result:")
                cryptogram = self.EncryptAES_CBC(message, key, iv)
                expectedCryptogram = self.tests[test]['expectedCryptogram']
                errorCount += self.TestAndAnnounce(cryptogram.hex(), expectedCryptogram)
                print('Decrypting...')
                decryptedMessage = self.DecryptAES_CBC(cryptogram, key, iv)
                print('Decrypted message:')
                errorCount += self.TestAndAnnounce(decryptedMessage, message)
        if(errorCount > 0):
            print('Tests Failed: {}'.format(errorCount))
        else:
            print('All tests passed.')


    def TestAndAnnounce(self, result, reference):
        print(result)
        if(reference == None):
            return 0
        if(result == reference):
            print("Correct!")
            return 0
        print("Incorrect! Expected:")
        print(reference)
        return 1
        

#TESTS
# trusted source: https://www.javainuse.com/aesgenerator  (expectecCryptograms are in hex format):
    tests = {
        "ECB": {
            "mode": "ECB",
            "key": "SuperSecret1234512345678",
            "initialValue": None,
            "message": "123456789ABCDEF123456789ABCDEF123456789AB",
            "expectedCryptogram": '2a6e8a3df1847ab182d035e3ef65b203bcaa495bafff5f75827329311e32d25e0a108e8bfbe29c32ab6e8aca6e97224f',
        },
        "CBC": {
            "mode": "CBC",
            "key": "SuperSecret1234512345678",
            "initialValue": "InitVarOLength16",
            "message": "123456789ABCDEF123456789ABCDEF123456789AB",
            "expectedCryptogram": '0966b37a583dcd2a6713ed3cd894301be1d8443f9ab2db2bc1e9677203a72beeb9d6b933b28724410e8740999b90cd10',
        },
        "ECB2": {
            "mode": "ECB",
            "key": "SuperSecret1234512345678",
            "initialValue": None,
            "message": "0123456789ABCDEF0123456789ABCDEF",
            "expectedCryptogram": 'e3aafb18e2d0b136ad6f1ef88ae17f70e3aafb18e2d0b136ad6f1ef88ae17f70ce4fefe9f0b28c56f665e9b0220f3dfd',
        },
        "CBC2": {
            "mode": "CBC",
            "key": "SuperSecret1234512345678",
            "initialValue": "InitV@rOLength16",
            "message": "0123456789ABCDEF0123456789ABCDEF",
            "expectedCryptogram": '1d841be87cb3b9df699f9415a47dbd9857a0c37b10011c544536929fb570ee76b10179e95e441ef4b19bd77a332e2ed6',
        },
        "ECB3": {
            "mode": "ECB",
            "key": "SuperSecret12345",
            "initialValue": None,
            "message": "Some secretive text that needs to be encrypted",
            "expectedCryptogram": '6c3e288541bca3a5a20056a4653d57470a3a9eb620116af6d46b6081cc8adbb1ff163ddf6f0a23202542b2c059dab5b4',
        },
        "CBC3": {
            "mode": "CBC",
            "key": "MegaMagicMystery",
            "initialValue": "16CharV@riable16",
            "message": "This text is not expected to be compared to anything, therefore it has no expectedCryptogram",
            "expectedCryptogram": None,
        },
        "TEST NAME": { 
            "mode": "CBC", 
            "key": "VALID_SECRET_KEY", 
            "initialValue": "16_CHAR_LONG_IV_", 
            "message": "Some message to encrypt", 
            "expectedCryptogram": None, # optional: 
     #visit “# trusted source” to quickly obtain a valid expected cryptogram 
        }, 
    }

class AES:

    expKey = []
    state = bytes(16)

    def AESEncrypt(self, message, key):

        # key expansion step - make a long, divided key form single input key
        self.expKey = self.AESKeyExpansion(key)

        # bytearray type because byte strings can't be modified
        self.state = bytearray(message)

        # initial transformation - 0th round key addition
        self.AESAddRoundKey(0)

        # how many rounds do we need
        n = len(key)
        MaxRounds = 10 if n == 16 else 12 if n == 24 else 14

        # main loop that goes through all the rounds but the last one
        for round in range(1, MaxRounds):
            self.AESSubBytes(0)
            self.AESShiftRows(0)
            self.AESMixColumns(0)
            self.AESAddRoundKey(round)

        # the last round
        round += 1
        self.AESSubBytes(0)
        self.AESShiftRows(0)
        self.AESAddRoundKey(round)

        # return ciphertext in the same type that input was received
        return bytes(self.state)

    def AESDecrypt(self, cryptogram, key):
        # key expansion step - make a long, divided key form single input key
        # the same expanded key is used in encryption and decryption
        self.expKey = self.AESKeyExpansion(key)

        # bytearray type because byte strings can't be modified
        self.state = bytearray(cryptogram)

        # how many rounds do we need
        n = len(key)
        MaxRounds = 10 if n == 16 else 12 if n == 24 else 14

        # initial transformation - MaxRounds-th round key addition
        # the round keys are added in reverse order on decryption
        self.AESAddRoundKey(MaxRounds)

        # main loop that goes through all the rounds but the last one
        # also backwards so that MixColumns takes correct parameter
        # since the function does not change for decryption
        for round in range(MaxRounds-1, 0, -1):
            self.AESShiftRows(1)
            self.AESSubBytes(1)
            self.AESAddRoundKey(round)
            self.AESMixColumns(1)

        # last round, 0th round key
        round -= 1
        self.AESShiftRows(1)
        self.AESSubBytes(1)
        self.AESAddRoundKey(round)

        # return ciphertext in the same type that input was received
        return bytes(self.state)

    def AESKeyExpansion(self, key):

        # split the key into list of words (4 bytes)
        keyRound = [key[i:i + 4] for i in range(0, len(key), 4)]

        # The first n bytes of the expanded key are simply the encryption key.
        # extKey indexes == rounds of expansion (not AES rounds!)
        extKey = []
        extKey.append(keyRound)
        round =0

        # how many words should the extended key have
        n = len(key)
        b = 44 if n == 16 else 52 if n == 24 else 60
        n = n//4

        # a double loop since extKey is a 2d list
        # this one appends rounds of words to extKey
        # (number of rounds depends on original key size)
        # until length of extended key is enough
        while len(sum(extKey, [])) < b :
            round += 1
            temp = extKey[round - 1][-1] #last of each word is used in first of next word
            keyRound = [] # holds words

            # this one adds words to keyRound
            for i in range (0, n):

                if i == 0:
                    # rotate the word 1 time
                    temp = rotateWord(temp, 1)

                    # substitute each byte using the sbox
                    temp = [s_box[i] for i in temp]

                    # xor the first byte of temp with rcon(round)
                    temp[0] ^= rcon[round]

                # word n in a round = word n from previous round XOR temp
                # temp is either a transformed last word of previous round,
                # if this is first word of a round,
                # or just previous word in a round
                keyRound.append(sxor(temp, extKey[round-1][i] ))

                # this word in a round is used for next word
                temp = keyRound[-1]

            extKey.append(keyRound)

        # turn extKey into one big list then split into 4-word rounds used for AES encryption
        extKey = sum(extKey, [])
        extKey = [extKey[i:i + 4] for i in range(0, len(extKey), 4)]

        return extKey

    def AESSubBytes(self, isInverse):
        # substitutes a byte in the state with a corresponding byte in the s_box.
        # this, unlike what is specified in the theory, does not determine the corresponding
        # byte by looking at bits;
        # instead, s_box is just a 1-dimensional array, with decimal numbers,
        # and the decimal value of the byte is passed as index for s_box.
        # this achieves the same result but is much easier to do.
        if isInverse == 0 : self.state = bytearray([s_box[i] for i in self.state])
        else: self.state = bytearray([inv_s_box[i] for i in self.state])

    def AESShiftRows(self, isInverse):
        # divide the state into rows
        temp = [self.state[i::4] for i in range(0, 4)]

        # shift each row. row 0 by 0 places, row 1 by 1, etc
        # to the left when encrypting, to the right when decrypting
        if isInverse == 0:
            for i in range(0, 4): temp[i] = rotateWord(temp[i], i)
        else:
            for i in range(0, 4): temp[i] = rotateWord(temp[i], -i)

        # join the rows back into the state byte array
        temp = b''.join(temp)
        temp = [temp[i::4] for i in range(0, 4)]
        self.state = bytearray(b''.join(temp))

    def AESMixColumns(self, isInverse):
        # divide the state into columns
        temp = [[0]*4 for i in range(4)]
        tempState = [list(self.state[i:i + 4]) for i in range(0, 16, 4)]

        # use the correct matrix depending on if encrypting or decrypting
        if isInverse == 0: matrix = MixColumnMatrix
        else: matrix = MixColumnMatrixInv

        # multiplication of each column of the state by the matrix.
        # it functions similarly to normal matrix multiplication, but the addition is XOR,
        # and multiplication is multiplication in finite field GF(2^8).
        # however, this function uses a method which is easier to program.
        # Since the matrix and the field are constant, we know the result of multiplication
        # for any byte- so it's possible to create lookup tables for each value from the matrix.
        # then, to get the value of a byte, it is enough to look up the result of multiplication
        # in the correct table, then xor the 4 values in the corresponding row together.
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    if matrix[j][k] == 2: temp[i][j] ^= galMul2[tempState[i][k]]
                    elif matrix[j][k] == 3: temp[i][j] ^= galMul3[tempState[i][k]]
                    elif matrix[j][k] == 9: temp[i][j] ^= galMul9[tempState[i][k]]
                    elif matrix[j][k] == 11: temp[i][j] ^= galMul11[tempState[i][k]]
                    elif matrix[j][k] == 13: temp[i][j] ^= galMul13[tempState[i][k]]
                    elif matrix[j][k] == 14: temp[i][j] ^= galMul14[tempState[i][k]]
                    else: temp[i][j] ^= tempState[i][k]

        self.state = bytearray(sum(temp, []))

    def AESAddRoundKey(self, round):
        # concatenates the key so its just a 16 byte string
        # then xors with corresponding byte from round key
        keyRound = b''.join(self.expKey[round])
        for i in range(0, 16): self.state[i] ^= keyRound[i]

# function that xors byte strings
def sxor(ba1, ba2):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

# shifts bytes in a word to the left (rotates the word) n times
def rotateWord(word, n):
    return word[n:] + word[:n]

    # The round constants used in key expansion.
    # rcon[0] is never actually used, while rcon[i] could also
    # be computed during runtime as AES.mul(1 << (i - 1), 1).

rcon = [0, 1, 2, 4, 8, 16, 32, 64, 128, 27, 54]

    # The S-box and inverse S-box used in SubBytes() and InvSubBytes().
s_box = [
         99, 124, 119, 123, 242, 107, 111, 197,  48,   1, 103,  43, 254, 215, 171, 118,
        202, 130, 201, 125, 250,  89,  71, 240, 173, 212, 162, 175, 156, 164, 114, 192,
        183, 253, 147,  38,  54,  63, 247, 204,  52, 165, 229, 241, 113, 216,  49,  21,
          4, 199,  35, 195,  24, 150,   5, 154,   7,  18, 128, 226, 235,  39, 178, 117,
          9, 131,  44,  26,  27, 110,  90, 160,  82,  59, 214, 179,  41, 227,  47, 132,
         83, 209,   0, 237,  32, 252, 177,  91, 106, 203, 190,  57,  74,  76,  88, 207,
        208, 239, 170, 251,  67,  77,  51, 133,  69, 249,   2, 127,  80,  60, 159, 168,
         81, 163,  64, 143, 146, 157,  56, 245, 188, 182, 218,  33,  16, 255, 243, 210,
        205,  12,  19, 236,  95, 151,  68,  23, 196, 167, 126,  61, 100,  93,  25, 115,
         96, 129,  79, 220,  34,  42, 144, 136,  70, 238, 184,  20, 222,  94,  11, 219,
        224,  50,  58,  10,  73,   6,  36,  92, 194, 211, 172,  98, 145, 149, 228, 121,
        231, 200,  55, 109, 141, 213,  78, 169, 108,  86, 244, 234, 101, 122, 174,   8,
        186, 120,  37,  46,  28, 166, 180, 198, 232, 221, 116,  31,  75, 189, 139, 138,
        112,  62, 181, 102,  72,   3, 246,  14,  97,  53,  87, 185, 134, 193,  29, 158,
        225, 248, 152,  17, 105, 217, 142, 148, 155,  30, 135, 233, 206,  85,  40, 223,
        140, 161, 137,  13, 191, 230,  66, 104,  65, 153,  45,  15, 176,  84, 187,  22,
    ]
inv_s_box = [
         82,   9, 106, 213,  48,  54, 165,  56, 191,  64, 163, 158, 129, 243, 215, 251,
        124, 227,  57, 130, 155,  47, 255, 135,  52, 142,  67,  68, 196, 222, 233, 203,
         84, 123, 148,  50, 166, 194,  35,  61, 238,  76, 149,  11,  66, 250, 195,  78,
          8,  46, 161, 102,  40, 217,  36, 178, 118,  91, 162,  73, 109, 139, 209,  37,
        114, 248, 246, 100, 134, 104, 152,  22, 212, 164,  92, 204,  93, 101, 182, 146,
        108, 112,  72,  80, 253, 237, 185, 218,  94,  21,  70,  87, 167, 141, 157, 132,
        144, 216, 171,   0, 140, 188, 211,  10, 247, 228,  88,   5, 184, 179,  69,   6,
        208,  44,  30, 143, 202,  63,  15,   2, 193, 175, 189,   3,   1,  19, 138, 107,
         58, 145,  17,  65,  79, 103, 220, 234, 151, 242, 207, 206, 240, 180, 230, 115,
        150, 172, 116,  34, 231, 173,  53, 133, 226, 249,  55, 232,  28, 117, 223, 110,
         71, 241,  26, 113,  29,  41, 197, 137, 111, 183,  98,  14, 170,  24, 190,  27,
        252,  86,  62,  75, 198, 210, 121,  32, 154, 219, 192, 254, 120, 205,  90, 244,
         31, 221, 168,  51, 136,   7, 199,  49, 177,  18,  16,  89,  39, 128, 236,  95,
         96,  81, 127, 169,  25, 181,  74,  13,  45, 229, 122, 159, 147, 201, 156, 239,
        160, 224,  59,  77, 174,  42, 245, 176, 200, 235, 187,  60, 131,  83, 153,  97,
         23,  43,   4, 126, 186, 119, 214,  38, 225, 105,  20,  99,  85,  33,  12, 125,
    ]

# matrices used by the MixColumn function, by which it multiplies the coulmns
MixColumnMatrix = [[2, 3, 1, 1], [1, 2, 3, 1], [1, 1, 2, 3], [3, 1, 1, 2]]
MixColumnMatrixInv = [[14, 11, 13, 9],[9, 14, 11, 13],[13, 9, 14, 11],[11, 13, 9, 14]]

# lookup tables used by the MixColumn function to make multiplication easier
galMul2 = list(bytes([
    0x00,0x02,0x04,0x06,0x08,0x0a,0x0c,0x0e,0x10,0x12,0x14,0x16,0x18,0x1a,0x1c,0x1e,
    0x20,0x22,0x24,0x26,0x28,0x2a,0x2c,0x2e,0x30,0x32,0x34,0x36,0x38,0x3a,0x3c,0x3e,
    0x40,0x42,0x44,0x46,0x48,0x4a,0x4c,0x4e,0x50,0x52,0x54,0x56,0x58,0x5a,0x5c,0x5e,
    0x60,0x62,0x64,0x66,0x68,0x6a,0x6c,0x6e,0x70,0x72,0x74,0x76,0x78,0x7a,0x7c,0x7e,
    0x80,0x82,0x84,0x86,0x88,0x8a,0x8c,0x8e,0x90,0x92,0x94,0x96,0x98,0x9a,0x9c,0x9e,
    0xa0,0xa2,0xa4,0xa6,0xa8,0xaa,0xac,0xae,0xb0,0xb2,0xb4,0xb6,0xb8,0xba,0xbc,0xbe,
    0xc0,0xc2,0xc4,0xc6,0xc8,0xca,0xcc,0xce,0xd0,0xd2,0xd4,0xd6,0xd8,0xda,0xdc,0xde,
    0xe0,0xe2,0xe4,0xe6,0xe8,0xea,0xec,0xee,0xf0,0xf2,0xf4,0xf6,0xf8,0xfa,0xfc,0xfe,
    0x1b,0x19,0x1f,0x1d,0x13,0x11,0x17,0x15,0x0b,0x09,0x0f,0x0d,0x03,0x01,0x07,0x05,
    0x3b,0x39,0x3f,0x3d,0x33,0x31,0x37,0x35,0x2b,0x29,0x2f,0x2d,0x23,0x21,0x27,0x25,
    0x5b,0x59,0x5f,0x5d,0x53,0x51,0x57,0x55,0x4b,0x49,0x4f,0x4d,0x43,0x41,0x47,0x45,
    0x7b,0x79,0x7f,0x7d,0x73,0x71,0x77,0x75,0x6b,0x69,0x6f,0x6d,0x63,0x61,0x67,0x65,
    0x9b,0x99,0x9f,0x9d,0x93,0x91,0x97,0x95,0x8b,0x89,0x8f,0x8d,0x83,0x81,0x87,0x85,
    0xbb,0xb9,0xbf,0xbd,0xb3,0xb1,0xb7,0xb5,0xab,0xa9,0xaf,0xad,0xa3,0xa1,0xa7,0xa5,
    0xdb,0xd9,0xdf,0xdd,0xd3,0xd1,0xd7,0xd5,0xcb,0xc9,0xcf,0xcd,0xc3,0xc1,0xc7,0xc5,
    0xfb,0xf9,0xff,0xfd,0xf3,0xf1,0xf7,0xf5,0xeb,0xe9,0xef,0xed,0xe3,0xe1,0xe7,0xe5]))
galMul3 = list(bytes([
    0x00,0x03,0x06,0x05,0x0c,0x0f,0x0a,0x09,0x18,0x1b,0x1e,0x1d,0x14,0x17,0x12,0x11,
    0x30,0x33,0x36,0x35,0x3c,0x3f,0x3a,0x39,0x28,0x2b,0x2e,0x2d,0x24,0x27,0x22,0x21,
    0x60,0x63,0x66,0x65,0x6c,0x6f,0x6a,0x69,0x78,0x7b,0x7e,0x7d,0x74,0x77,0x72,0x71,
    0x50,0x53,0x56,0x55,0x5c,0x5f,0x5a,0x59,0x48,0x4b,0x4e,0x4d,0x44,0x47,0x42,0x41,
    0xc0,0xc3,0xc6,0xc5,0xcc,0xcf,0xca,0xc9,0xd8,0xdb,0xde,0xdd,0xd4,0xd7,0xd2,0xd1,
    0xf0,0xf3,0xf6,0xf5,0xfc,0xff,0xfa,0xf9,0xe8,0xeb,0xee,0xed,0xe4,0xe7,0xe2,0xe1,
    0xa0,0xa3,0xa6,0xa5,0xac,0xaf,0xaa,0xa9,0xb8,0xbb,0xbe,0xbd,0xb4,0xb7,0xb2,0xb1,
    0x90,0x93,0x96,0x95,0x9c,0x9f,0x9a,0x99,0x88,0x8b,0x8e,0x8d,0x84,0x87,0x82,0x81,
    0x9b,0x98,0x9d,0x9e,0x97,0x94,0x91,0x92,0x83,0x80,0x85,0x86,0x8f,0x8c,0x89,0x8a,
    0xab,0xa8,0xad,0xae,0xa7,0xa4,0xa1,0xa2,0xb3,0xb0,0xb5,0xb6,0xbf,0xbc,0xb9,0xba,
    0xfb,0xf8,0xfd,0xfe,0xf7,0xf4,0xf1,0xf2,0xe3,0xe0,0xe5,0xe6,0xef,0xec,0xe9,0xea,
    0xcb,0xc8,0xcd,0xce,0xc7,0xc4,0xc1,0xc2,0xd3,0xd0,0xd5,0xd6,0xdf,0xdc,0xd9,0xda,
    0x5b,0x58,0x5d,0x5e,0x57,0x54,0x51,0x52,0x43,0x40,0x45,0x46,0x4f,0x4c,0x49,0x4a,
    0x6b,0x68,0x6d,0x6e,0x67,0x64,0x61,0x62,0x73,0x70,0x75,0x76,0x7f,0x7c,0x79,0x7a,
    0x3b,0x38,0x3d,0x3e,0x37,0x34,0x31,0x32,0x23,0x20,0x25,0x26,0x2f,0x2c,0x29,0x2a,
    0x0b,0x08,0x0d,0x0e,0x07,0x04,0x01,0x02,0x13,0x10,0x15,0x16,0x1f,0x1c,0x19,0x1a]))
galMul9 = list(bytes([
    0x00,0x09,0x12,0x1b,0x24,0x2d,0x36,0x3f,0x48,0x41,0x5a,0x53,0x6c,0x65,0x7e,0x77,
    0x90,0x99,0x82,0x8b,0xb4,0xbd,0xa6,0xaf,0xd8,0xd1,0xca,0xc3,0xfc,0xf5,0xee,0xe7,
    0x3b,0x32,0x29,0x20,0x1f,0x16,0x0d,0x04,0x73,0x7a,0x61,0x68,0x57,0x5e,0x45,0x4c,
    0xab,0xa2,0xb9,0xb0,0x8f,0x86,0x9d,0x94,0xe3,0xea,0xf1,0xf8,0xc7,0xce,0xd5,0xdc,
    0x76,0x7f,0x64,0x6d,0x52,0x5b,0x40,0x49,0x3e,0x37,0x2c,0x25,0x1a,0x13,0x08,0x01,
    0xe6,0xef,0xf4,0xfd,0xc2,0xcb,0xd0,0xd9,0xae,0xa7,0xbc,0xb5,0x8a,0x83,0x98,0x91,
    0x4d,0x44,0x5f,0x56,0x69,0x60,0x7b,0x72,0x05,0x0c,0x17,0x1e,0x21,0x28,0x33,0x3a,
    0xdd,0xd4,0xcf,0xc6,0xf9,0xf0,0xeb,0xe2,0x95,0x9c,0x87,0x8e,0xb1,0xb8,0xa3,0xaa,
    0xec,0xe5,0xfe,0xf7,0xc8,0xc1,0xda,0xd3,0xa4,0xad,0xb6,0xbf,0x80,0x89,0x92,0x9b,
    0x7c,0x75,0x6e,0x67,0x58,0x51,0x4a,0x43,0x34,0x3d,0x26,0x2f,0x10,0x19,0x02,0x0b,
    0xd7,0xde,0xc5,0xcc,0xf3,0xfa,0xe1,0xe8,0x9f,0x96,0x8d,0x84,0xbb,0xb2,0xa9,0xa0,
    0x47,0x4e,0x55,0x5c,0x63,0x6a,0x71,0x78,0x0f,0x06,0x1d,0x14,0x2b,0x22,0x39,0x30,
    0x9a,0x93,0x88,0x81,0xbe,0xb7,0xac,0xa5,0xd2,0xdb,0xc0,0xc9,0xf6,0xff,0xe4,0xed,
    0x0a,0x03,0x18,0x11,0x2e,0x27,0x3c,0x35,0x42,0x4b,0x50,0x59,0x66,0x6f,0x74,0x7d,
    0xa1,0xa8,0xb3,0xba,0x85,0x8c,0x97,0x9e,0xe9,0xe0,0xfb,0xf2,0xcd,0xc4,0xdf,0xd6,
    0x31,0x38,0x23,0x2a,0x15,0x1c,0x07,0x0e,0x79,0x70,0x6b,0x62,0x5d,0x54,0x4f,0x46]))
galMul11 = list(bytes([
    0x00,0x0b,0x16,0x1d,0x2c,0x27,0x3a,0x31,0x58,0x53,0x4e,0x45,0x74,0x7f,0x62,0x69,
    0xb0,0xbb,0xa6,0xad,0x9c,0x97,0x8a,0x81,0xe8,0xe3,0xfe,0xf5,0xc4,0xcf,0xd2,0xd9,
    0x7b,0x70,0x6d,0x66,0x57,0x5c,0x41,0x4a,0x23,0x28,0x35,0x3e,0x0f,0x04,0x19,0x12,
    0xcb,0xc0,0xdd,0xd6,0xe7,0xec,0xf1,0xfa,0x93,0x98,0x85,0x8e,0xbf,0xb4,0xa9,0xa2,
    0xf6,0xfd,0xe0,0xeb,0xda,0xd1,0xcc,0xc7,0xae,0xa5,0xb8,0xb3,0x82,0x89,0x94,0x9f,
    0x46,0x4d,0x50,0x5b,0x6a,0x61,0x7c,0x77,0x1e,0x15,0x08,0x03,0x32,0x39,0x24,0x2f,
    0x8d,0x86,0x9b,0x90,0xa1,0xaa,0xb7,0xbc,0xd5,0xde,0xc3,0xc8,0xf9,0xf2,0xef,0xe4,
    0x3d,0x36,0x2b,0x20,0x11,0x1a,0x07,0x0c,0x65,0x6e,0x73,0x78,0x49,0x42,0x5f,0x54,
    0xf7,0xfc,0xe1,0xea,0xdb,0xd0,0xcd,0xc6,0xaf,0xa4,0xb9,0xb2,0x83,0x88,0x95,0x9e,
    0x47,0x4c,0x51,0x5a,0x6b,0x60,0x7d,0x76,0x1f,0x14,0x09,0x02,0x33,0x38,0x25,0x2e,
    0x8c,0x87,0x9a,0x91,0xa0,0xab,0xb6,0xbd,0xd4,0xdf,0xc2,0xc9,0xf8,0xf3,0xee,0xe5,
    0x3c,0x37,0x2a,0x21,0x10,0x1b,0x06,0x0d,0x64,0x6f,0x72,0x79,0x48,0x43,0x5e,0x55,
    0x01,0x0a,0x17,0x1c,0x2d,0x26,0x3b,0x30,0x59,0x52,0x4f,0x44,0x75,0x7e,0x63,0x68,
    0xb1,0xba,0xa7,0xac,0x9d,0x96,0x8b,0x80,0xe9,0xe2,0xff,0xf4,0xc5,0xce,0xd3,0xd8,
    0x7a,0x71,0x6c,0x67,0x56,0x5d,0x40,0x4b,0x22,0x29,0x34,0x3f,0x0e,0x05,0x18,0x13,
    0xca,0xc1,0xdc,0xd7,0xe6,0xed,0xf0,0xfb,0x92,0x99,0x84,0x8f,0xbe,0xb5,0xa8,0xa3]))
galMul13 = list(bytes([
    0x00,0x0d,0x1a,0x17,0x34,0x39,0x2e,0x23,0x68,0x65,0x72,0x7f,0x5c,0x51,0x46,0x4b,
    0xd0,0xdd,0xca,0xc7,0xe4,0xe9,0xfe,0xf3,0xb8,0xb5,0xa2,0xaf,0x8c,0x81,0x96,0x9b,
    0xbb,0xb6,0xa1,0xac,0x8f,0x82,0x95,0x98,0xd3,0xde,0xc9,0xc4,0xe7,0xea,0xfd,0xf0,
    0x6b,0x66,0x71,0x7c,0x5f,0x52,0x45,0x48,0x03,0x0e,0x19,0x14,0x37,0x3a,0x2d,0x20,
    0x6d,0x60,0x77,0x7a,0x59,0x54,0x43,0x4e,0x05,0x08,0x1f,0x12,0x31,0x3c,0x2b,0x26,
    0xbd,0xb0,0xa7,0xaa,0x89,0x84,0x93,0x9e,0xd5,0xd8,0xcf,0xc2,0xe1,0xec,0xfb,0xf6,
    0xd6,0xdb,0xcc,0xc1,0xe2,0xef,0xf8,0xf5,0xbe,0xb3,0xa4,0xa9,0x8a,0x87,0x90,0x9d,
    0x06,0x0b,0x1c,0x11,0x32,0x3f,0x28,0x25,0x6e,0x63,0x74,0x79,0x5a,0x57,0x40,0x4d,
    0xda,0xd7,0xc0,0xcd,0xee,0xe3,0xf4,0xf9,0xb2,0xbf,0xa8,0xa5,0x86,0x8b,0x9c,0x91,
    0x0a,0x07,0x10,0x1d,0x3e,0x33,0x24,0x29,0x62,0x6f,0x78,0x75,0x56,0x5b,0x4c,0x41,
    0x61,0x6c,0x7b,0x76,0x55,0x58,0x4f,0x42,0x09,0x04,0x13,0x1e,0x3d,0x30,0x27,0x2a,
    0xb1,0xbc,0xab,0xa6,0x85,0x88,0x9f,0x92,0xd9,0xd4,0xc3,0xce,0xed,0xe0,0xf7,0xfa,
    0xb7,0xba,0xad,0xa0,0x83,0x8e,0x99,0x94,0xdf,0xd2,0xc5,0xc8,0xeb,0xe6,0xf1,0xfc,
    0x67,0x6a,0x7d,0x70,0x53,0x5e,0x49,0x44,0x0f,0x02,0x15,0x18,0x3b,0x36,0x21,0x2c,
    0x0c,0x01,0x16,0x1b,0x38,0x35,0x22,0x2f,0x64,0x69,0x7e,0x73,0x50,0x5d,0x4a,0x47,
    0xdc,0xd1,0xc6,0xcb,0xe8,0xe5,0xf2,0xff,0xb4,0xb9,0xae,0xa3,0x80,0x8d,0x9a,0x97]))
galMul14 = list(bytes([
    0x00,0x0e,0x1c,0x12,0x38,0x36,0x24,0x2a,0x70,0x7e,0x6c,0x62,0x48,0x46,0x54,0x5a,
    0xe0,0xee,0xfc,0xf2,0xd8,0xd6,0xc4,0xca,0x90,0x9e,0x8c,0x82,0xa8,0xa6,0xb4,0xba,
    0xdb,0xd5,0xc7,0xc9,0xe3,0xed,0xff,0xf1,0xab,0xa5,0xb7,0xb9,0x93,0x9d,0x8f,0x81,
    0x3b,0x35,0x27,0x29,0x03,0x0d,0x1f,0x11,0x4b,0x45,0x57,0x59,0x73,0x7d,0x6f,0x61,
    0xad,0xa3,0xb1,0xbf,0x95,0x9b,0x89,0x87,0xdd,0xd3,0xc1,0xcf,0xe5,0xeb,0xf9,0xf7,
    0x4d,0x43,0x51,0x5f,0x75,0x7b,0x69,0x67,0x3d,0x33,0x21,0x2f,0x05,0x0b,0x19,0x17,
    0x76,0x78,0x6a,0x64,0x4e,0x40,0x52,0x5c,0x06,0x08,0x1a,0x14,0x3e,0x30,0x22,0x2c,
    0x96,0x98,0x8a,0x84,0xae,0xa0,0xb2,0xbc,0xe6,0xe8,0xfa,0xf4,0xde,0xd0,0xc2,0xcc,
    0x41,0x4f,0x5d,0x53,0x79,0x77,0x65,0x6b,0x31,0x3f,0x2d,0x23,0x09,0x07,0x15,0x1b,
    0xa1,0xaf,0xbd,0xb3,0x99,0x97,0x85,0x8b,0xd1,0xdf,0xcd,0xc3,0xe9,0xe7,0xf5,0xfb,
    0x9a,0x94,0x86,0x88,0xa2,0xac,0xbe,0xb0,0xea,0xe4,0xf6,0xf8,0xd2,0xdc,0xce,0xc0,
    0x7a,0x74,0x66,0x68,0x42,0x4c,0x5e,0x50,0x0a,0x04,0x16,0x18,0x32,0x3c,0x2e,0x20,
    0xec,0xe2,0xf0,0xfe,0xd4,0xda,0xc8,0xc6,0x9c,0x92,0x80,0x8e,0xa4,0xaa,0xb8,0xb6,
    0x0c,0x02,0x10,0x1e,0x34,0x3a,0x28,0x26,0x7c,0x72,0x60,0x6e,0x44,0x4a,0x58,0x56,
    0x37,0x39,0x2b,0x25,0x0f,0x01,0x13,0x1d,0x47,0x49,0x5b,0x55,0x7f,0x71,0x63,0x6d,
    0xd7,0xd9,0xcb,0xc5,0xef,0xe1,0xf3,0xfd,0xa7,0xa9,0xbb,0xb5,0x9f,0x91,0x83,0x8d]))

# run the program
p = AES_Program()
p.Tests()