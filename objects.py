import numpy as np


class LatexObject(object):

    def __init__(self):
        self.texLines = []  # the main list
        self._caption = False
        self._label = False

    def _startObject(self):
        return ['']

    def _endObject(self):
        return ['']

    def _proccessTex(self):
        return self.texLines

    def addCaption(self, caption):
        self._caption = '\\caption{' + caption + '}'

    def addLabel(self, label):
        self._label = '\\label{' + label + '}'

    def output(self):
        """ outputs tex as a string
        """
        texFile = '\n'.join(self._startObject() + self.texLines + self._endObject())

        return texFile


class MultiFigure(LatexObject):
    """ Handles a multiple plots in a figure instance
    """

    def __init__(self, pos='htbp', figsPerRow=2):
        LatexObject.__init__(self)

        self.pos = pos  # position argument
        self.centering = True
        self.figsPerRow = figsPerRow
        self.maxWidthUnit = '\\textwidth'
        self.maxWidth = 1.0/figsPerRow

        # internal variables for code only
        self._figColNum = 1

    def _getWidth(self):
        return '{}{}'.format(self.maxWidth, self.maxWidthUnit)

    def addFigure(self, path):
        figColNum = self._figColNum
        # TODO complicated code can be replaced by ' & '.join (possibly)
        if len(self.texLines):  # if we have a previous figure
            if figColNum > 1:  # not the first in the row
                self.texLines[-1] += '&'  # add endchar to previous figure now we are adding another fig

        if figColNum < self.figsPerRow:
            self._figColNum += 1
            endChar = ''
        elif figColNum == self.figsPerRow:
            endChar = '\\\\'  # add end row char if last in row
            self._figColNum = 1
        else:
            raise ValueError('somethings wrong with the figure count')

        figureTex = '\includegraphics[width={}]{}'.format(self._getWidth(), '{' + path + '}')
        self.texLines.append(figureTex + endChar)

    def _startObject(self):
        startObject= ['\\begin{figure}[' + self.pos + ']']
        if self._caption:
            startObject.append(self._caption)
        if self.centering:
            startObject.append('\\centering')
        startObject.append('\\begin{{tabular}}{{{}}}'.format('c' * self.figsPerRow))
        return startObject

    def _endObject(self):
        endObject = ['\\end{tabular}']
        if self._label:
            endObject.append(self._label)
        endObject.append('\\end{figure}')
        return endObject


class Table(LatexObject):
    """ Handles a table instance
    """

    def __init__(self, columns):
        LatexObject.__init__(self)

        self.columns = columns
        self.pos = 'htbp'
        self.centering = True

        self._header = False
        self._layout = False  # allows setting of manual layout

        # Hooks
        self.hook_BeforeTableStart = []
        self._blankchar = '~'

    def _startObject(self):
        startObject= ['\\begin{table}[' + self.pos + ']']
        if self._caption:
            startObject.append(self._caption)
        if self.centering:
            startObject.append('\\centering')

        if self.hook_BeforeTableStart:  # Hook
            startObject += self.hook_BeforeTableStart

        if self._layout:
            layout = self._layout
        else:
            layout = 'l' * self.columns
        startObject.append('\\begin{tabular}{' + layout + '}')

        if self._header:
            startObject.append(self._header)
            startObject.append('\hline')

        return startObject

    def addRow(self, rowList):

        if len(rowList) != self.columns:
            raise ValueError('You must give the exact number of columns each time (set {} got {}).'
                             ' use np.nan for blanks'.format(self.columns, len(rowList)))

        parsedRowList = [self._blankchar if str(val) == 'nan' else str(val) for val in rowList]  # math.nan will fail is non float, np.nan only catches numpy nans
        self.texLines.append(' & '.join(parsedRowList) + ' \\\\')  # seperate values by & next cell char and lines by new line\\

    def _endObject(self):
        endObject = ['\\end{tabular}']
        if self._label:
            endObject.append(self._label)
        endObject.append('\\end{table}')
        return endObject

    def addHeader(self, headerList):
        """ Currently you can only have one header, it will be seperated from the rest by a line and will replace any
        existing header
        """

        # for ease and to avoid extra function calls just add row then pop it into the header

        self.addRow(headerList)
        self._header = self.texLines.pop()


class LongTable(Table):
    """ Handles a long table instance, in this class header is the all pages header
    """

    def __init__(self, columns):
        Table.__init__(self, columns)

        self._pageHeaderLabel = False
        self._firstPageHeader = False
        self._footer = False
        self._lastPageFooter = False

    def addFirstPageHeader(self, headerList):
        """ Currently this is your caption + table headings
        """
        raise NotImplementedError

    def addPageHeaderLabel(self, headerLabel="\\tablename\ \\thetable\ -- \\textit{Continued from previous page}"):
        """ i.e. continued from last page
        """
        self._pageHeaderLabel = '\multicolumn{{{}}}{{l}}{{{}}}'.format(self.columns, headerLabel)

    def addLastPageFooter(self, footertext):
        self._lastPageFooter = footertext

    def addFooter(self, footertext="\\textit{Continued on next page}"):
        """ normally a label i.e. (continued on next page)
        """
        self._footer = '\multicolumn{{{}}}{{l}}{{{}}}'.format(self.columns, footertext)

    def _startObject(self):
        if self._layout:
            layout = self._layout
        else:
            layout = 'l' * self.columns

        startObject = ['\\begin{longtable}[' + self.pos + ']{' + layout + '}']

        # First Page Header
        if self._caption:
            startObject += [self._caption + '\\\\', '\\hline']  # caption has no linebreak by efault unlike addrow
            if self._header:
                startObject += [self._header, '\\hline']

            startObject.append("\endfirsthead")

        # Every other page Header
        if self._header:
            if self._pageHeaderLabel:
                startObject.append(self._pageHeaderLabel + '\\\\')
            startObject += ['\\hline', self._header, '\\hline', '\endhead']
        elif self._pageHeaderLabel:
            startObject += [self._pageHeaderLabel + '\\\\', '\\hline', '\endhead']

        if self._footer:
            startObject += [self._footer + '\\\\', '\endfoot']

        if self._lastPageFooter:
            startObject += ['\\hline', self._lastPageFooter + '\\\\', '\endlastfoot']

        if self.hook_BeforeTableStart:  # Hook
            startObject += self.hook_BeforeTableStart

        return startObject

    def _endObject(self):
        endObject = []
        if self._label:
            endObject.append(self._label)
        endObject.append('\\end{longtable}')
        return endObject