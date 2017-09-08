from time import gmtime, strftime

class PrintHelper(object):  
    #print parameter
    PRINT_CONTENT_ID_CHAR_LIMIT = 5
    PRINT_INDENT_NUM_SPACE      = 2

    def print(str , numIndent=0):
        indent = " " * (PrintHelper.PRINT_INDENT_NUM_SPACE * (numIndent+1))
 
        print (strftime("%H:%M:%S", gmtime())+" ", end='')
        print(indent, end='')    
        
        print (str)