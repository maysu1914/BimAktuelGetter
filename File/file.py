class File:
    filename = 'file'

    def __init__(self, filename=filename):
        self.filename = filename
        self.append_to_filename()

    def append_to_filename(self):
        self.filename += input('Filename: {}'.format(self.filename))

    def export(self, data):
        with open('{name}.txt'.format(name=self.filename), 'w', encoding='utf-8') as file:
            file.write(data)
        print('\n{name}.txt created.'.format(name=self.filename))