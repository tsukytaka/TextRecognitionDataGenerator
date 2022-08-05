from matplotlib import image
from PIL import Image
import bitstring
import jaconv

DATA_DIR_ROOT = '../../BillParcelOCR/TrainHWJapanese/Data/ETLCDB/'
# DEF_YAML_PATH = '../../ligua/BillParcelOCR/Data/ETLCDB/etl_data_def.yml'
NUMBER_RECORD = 160

# char_dict = None
data_format = None

class ETLn_Record:
    def read(self, bs, pos=None):
        if pos:
            bs.bytepos = pos * self.octets_per_record

        r = bs.readlist(self.bitstring)

        record = dict(zip(self.fields, r))

        self.record = {
            k: (self.converter[k](v) if k in self.converter else v)
            for k, v in record.items()
        }

        return self.record

    def get_image(self):
        return self.record['Image Data']

class ETL167_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 2052
        self.fields = [
            "Data Number", "Character Code", "Serial Sheet Number", "JIS Code", "EBCDIC Code",
            "Evaluation of Individual Character Image", "Evaluation of Character Group",
            "Male-Female Code", "Age of Writer", "Serial Data Number",
            "Industry Classification Code", "Occupation Classification Code",
            "Sheet Gatherring Date", "Scanning Date",
            "Sample Position Y on Sheet", "Sample Position X on Sheet",
            "Minimum Scanned Level", "Maximum Scanned Level", "Image Data"
        ]
        self.bitstring = 'uint:16,bytes:2,uint:16,hex:8,hex:8,4*uint:8,uint:32,4*uint:16,4*uint:8,pad:32,bytes:2016,pad:32'
        self.converter = {
            'Character Code': lambda x: x.decode('ascii'),
            'Image Data': lambda x: Image.eval(Image.frombytes('F', (64, 63), x, 'bit', 4).convert('L'),
                                               lambda x: x * 16)
        }

    def get_char(self):
        return bytes.fromhex(self.record['JIS Code']).decode('shift_jis')

class ETL8G_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 8199
        self.fields = [
            "Serial Sheet Number", "JIS Kanji Code", "JIS Typical Reading", "Serial Data Number",
            "Evaluation of Individual Character Image", "Evaluation of Character Group",
            "Male-Female Code", "Age of Writer",
            "Industry Classification Code", "Occupation Classification Code",
            "Sheet Gatherring Date", "Scanning Date",
            "Sample Position X on Sheet", "Sample Position Y on Sheet", "Image Data"
        ]
        self.bitstring = 'uint:16,hex:16,bytes:8,uint:32,4*uint:8,4*uint:16,2*uint:8,pad:240,bytes:8128,pad:88'
        self.converter = {
            'JIS Typical Reading': lambda x: x.decode('ascii'),
            'Image Data': lambda x: Image.eval(Image.frombytes('F', (128, 127), x, 'bit', 4).convert('L'),
            lambda x: x * 16)
        }
    
    def get_char(self):
        char = bytes.fromhex(
            '1b2442' + self.record['JIS Kanji Code'] + '1b2842').decode('iso2022_jp')
        return char

class ETL9G_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 8199
        self.fields = [
            "Serial Sheet Number", "JIS Kanji Code", "JIS Typical Reading", "Serial Data Number",
            "Evaluation of Individual Character Image", "Evaluation of Character Group",
            "Male-Female Code", "Age of Writer",
            "Industry Classification Code", "Occupation Classification Code",
            "Sheet Gatherring Date", "Scanning Date",
            "Sample Position X on Sheet", "Sample Position Y on Sheet", "Image Data"
        ]
        self.bitstring = 'uint:16,hex:16,bytes:8,uint:32,4*uint:8,4*uint:16,2*uint:8,pad:272,bytes:8128,pad:56'
        self.converter = {
            'JIS Typical Reading': lambda x: x.decode('ascii'),
            'Image Data': lambda x: Image.eval(Image.frombytes('F', (128, 127), x, 'bit', 4).convert('L'),
                                               lambda x: x * 16)
        }

    def get_char(self):
        char = bytes.fromhex(
            '1b2442' + self.record['JIS Kanji Code'] + '1b2842').decode('iso2022_jp')
        return char

def read_chars(filename):
    text_file= open(filename,'r')
    data=text_file.read()
    return "".join(data.split())

char_dict_8G = {}
char_dict_9G = {}
char_dict_1C = {}
char_latin_dict_1C = {}

def generate(text, text_color, count):
    if len(char_latin_dict_1C) == 0:
        chars = read_chars(DATA_DIR_ROOT + 'ETL1/chars_latin.txt')
        print("number char latin 1C = ", len(chars))
        for i in range(len(chars)):
            char_latin_dict_1C[chars[i]] = i
    if len(char_dict_1C) == 0:
        chars = read_chars(DATA_DIR_ROOT + 'ETL1/chars.txt')
        print("number char 1C = ", len(chars))
        for i in range(len(chars)):
            char_dict_1C[chars[i]] = i
    if len(char_dict_8G) == 0:
        chars = read_chars(DATA_DIR_ROOT + 'ETL8G/chars.txt')
        print("number char 8G = ", len(chars))
        for i in range(len(chars)):
            char_dict_8G[chars[i]] = i
    if len(char_dict_9G) == 0:
        chars = read_chars(DATA_DIR_ROOT + 'ETL9G/chars.txt')
        print("number char 9G = ", len(chars))
        for i in range(len(chars)):
            char_dict_9G[chars[i]] = i
    
    
    images=[]
    for k in range(len(text)):
        if text[k] in char_latin_dict_1C:
            indexDataFile = char_dict_1C[text[k]] // 8
            dataFile = DATA_DIR_ROOT + 'ETL1/ETL1C_{:02d}'.format(indexDataFile)
            print("dataFile = ", dataFile)
            etln_record = ETL167_Record()
            index = count + 1411*(char_dict_1C[text[k]]%8)
            print("index=", index)
            f = bitstring.ConstBitStream(filename=dataFile)
            record = etln_record.read(f, index)
            char = etln_record.get_char()
            img = etln_record.get_image()
            images.append(img)
        elif text[k] in char_dict_1C:
            indexDataFile = char_dict_1C[text[k]] // 8 + 7
            dataFile = DATA_DIR_ROOT + 'ETL1/ETL1C_{:02d}'.format(indexDataFile)
            print("dataFile = ", dataFile)
            etln_record = ETL167_Record()
            index = count + 1411*(char_dict_1C[text[k]]%8)
            if (indexDataFile == 9 and char_dict_1C[text[k]] > char_dict_1C['ナ']) \
            or (indexDataFile == 12 and char_dict_1C[text[k]] > char_dict_1C['リ']):
                index -= 1
            print("index=", index)
            f = bitstring.ConstBitStream(filename=dataFile)
            record = etln_record.read(f, index)
            char = etln_record.get_char()
            img = etln_record.get_image()
            images.append(img)

        elif text[k] in char_dict_8G:
            indexDataFile = count // 5 + 1
            dataFile = DATA_DIR_ROOT + 'ETL8G/ETL8G_{:02d}'.format(indexDataFile)
            print("dataFile = ", dataFile)
            etln_record = ETL8G_Record()
            index = char_dict_8G[text[k]] + 956*(count%5)
            print("index=", index)
            f = bitstring.ConstBitStream(filename=dataFile)
            record = etln_record.read(f, index)
            char = etln_record.get_char()
            img = etln_record.get_image()
            images.append(img)
        
        elif text[k] in char_dict_9G:
            indexDataFile = count // 4 + 1
            dataFile = DATA_DIR_ROOT + 'ETL9G/ETL9G_{:02d}'.format(indexDataFile)
            print("dataFile = ", dataFile)
            etln_record = ETL9G_Record()
            index = char_dict_9G[text[k]] + 3036*(count%4)
            print("index=", index)
            f = bitstring.ConstBitStream(filename=dataFile)
            record = etln_record.read(f, index)
            char = etln_record.get_char()
            img = etln_record.get_image()
            images.append(img)

        elif text[k] in char_dict_1C:
            etln_record = ETL167_Record()
        else:
            images.clear()
            break
    if len(images) > 0:
        w, h = 64, 63 #images[0].width, images[0].height
        tiled = Image.new(images[0].mode, (w * len(text), h))
        for l in range(len(images)):
            img = Image.eval(images[l], lambda x: 255 - x)
            img = img.resize([w, h])
            tiled.paste(img, (w * l, 0))
        # tiled.save("tiledfn.png")
        #create RGBA image and RGB mask
        image = tiled.convert("RGBA") #Image.new("RGBA", (tiled.width, tiled.height), (0,0,0,0))
        datas = image.getdata()
        newData = []
        for item in datas:
            if item[0] >= 250 and item[1] >= 250 and item[2] >= 250:
                newData.append((item[0], item[1], item[2], 0))
            else:
                newData.append(item)
        image.putdata(newData)
        mask = tiled.convert("RGB")#Image.new("RGB", (tiled.width, tiled.height), (0, 0, 0))
    else:
        print("cannot generate this text: ", text)
        image = Image.new("RGBA", (50, 50), (0,0,0,0))
        mask = Image.new("RGB", (50, 50), (0, 0, 0))

    return image, mask