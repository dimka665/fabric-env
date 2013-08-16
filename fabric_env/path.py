# coding=utf-8

import os

# os.path.sep = '/'   # если вдруг генерируем пути в Windows, а используем в Linux


def join_paths(paths):
    paths = map(unicode, paths)  # чтобы не сработал Path.__add__
    # paths = map(str, paths)  # чтобы не сработал Path.__add__
    path = os.path.join(*paths)
    path = os.path.normpath(path)
    # path = path.replace(u'\\', u'/')   # если вдруг генерируем пути в Windows, а используем в Linux
    return path


# todo переписать и сделать атрибуты пропертями?
class Path(unicode):
# class Path(str):
    """File system path"""

    def __new__(cls, *paths, **kwargs):
        # объединяем параметры (str или Path) функцией join_paths
        return super(Path, cls).__new__(cls, join_paths(paths))

    def __init__(self, *paths, **kwargs):
        super(Path, self).__init__(*paths, **kwargs)

        self.__dict__['attrs'] = dict()

        children_from = kwargs.get('children', {})
        children = {}

        # если потомком, которых надо "унаследовать" не передали, то по возможности берем потомков последнего аргумента
        if 'children' not in kwargs:
            if len(paths) > 0:
                children_from = paths[-1]

        if hasattr(children_from, 'attrs'):
            children = children_from.attrs

        # добавляем потомков
        self.attrs.update(children)
        self.__dict__['parent'] = kwargs.get('parent', None)

    def __add__(self, other):
        return Path(self, other)

    def __div__(self, other):
        return Path(self, other)

    @classmethod
    def rel(cls, *args):
        folder = os.path.split(args[0])[0]
        return Path(folder, *args[1:])



    # todo может стоить удалить метод? тогда поведение сведется к поведению обычной строки
    # def __radd__(self, other):
    #     return Path(other, self)

    # a_b = a.b    =>    a_b = Path(a, b, parent=b)
    # then if: a_b.c = 'more'    =>    b.c = 'more'
    def __getattr__(self, key):
        if key in self.attrs:
            child = self.attrs[key]
        else:
            raise AttributeError(key)
        return Path(self, child, parent=child)

    def __setattr__(self, child_key, value):
        # если надо "переписать" потомка (а он может быть "в середине" и иметь потомков),
        # то передаем его потомков в новый Path в качестве потомков
        if child_key in self.attrs:
            # grandchildren = self.attrs[child_key].attrs
            grandchildren = self.attrs[child_key]
            child = Path(value, children=grandchildren)
        else:
            child = Path(value)

        self.attrs[child_key] = child

        # если мы знаем своего настоящего отца, то создаем потомка и ему)
        if self.parent:
            self.parent.attrs[child_key] = child

    def all(self):
        return self + '*'

    def mkfile(self):
        open(self, 'wb').close()

    # добавляем функции из стандартной библиотеки в качестве методов
    isdir = os.path.isdir
    isfile = os.path.isfile

    def mkdir(self):
        return os.mkdir(self)

    def dirname(self):
        return Path(os.path.dirname(self))

    # не доделано, нельзя использовать
    # обход дерева путей
    # def as_dict(self, key):
    #     paths = {}
    #     for sub_key, sub_path in self._children.items():
    #         new_key = key + '.' + sub_key
    #         print('new_key', new_key, self, sub_path, self + sub_path)
    #         paths[new_key] = self + sub_path
    #
    #         if sub_path._children:
    #             paths.update(self.as_dict(new_key))
    #     return paths

# Descriptor for 1st variant
class Root():
    def __init__(self):
        self.root = Path()

    def __set__(self, instance, value):
        self.root

class Pathed():

    def __init__(self):
        self.root = self.roooot + '.'

    def __setattr__(self, key, value):
        if key == 'root':
            self.__dict__['root'] = Path(value, children=self.root.attrs)


# 2nd variant - Path-Descriptor
def create_path_2(paths, rel_paths={}, parent=None):
    if isinstance(paths, (list, tuple)):
        pass
    else:
        paths = [paths]

    rel_paths = {key: PathDescriptor(value) for key, value in rel_paths.items() if not key.startswith('_')}
    if parent:
        rel_paths['_parent'] = parent

    # klass = type('Path', (str, Path_2), rel_paths)
    klass = type('Path_2', (PathDescriptor,), rel_paths)
    return klass(paths)


class PathDescriptor(str):
    # @classmethod
    # def get_descr(cls, key):
    #     return getattr('')
    #
    # def set_descr(cls, key, value):
    #     setattr(cls, key,

    # def __new__(cls, *args, **kwargs):
    def __new__(cls, paths):
        return str.__new__(cls, cls.join_paths(paths))

    # def __new__(cls, paths, rel_paths={}):
    #     rel_paths = {key: PathDescriptor(value) for key, value in rel_paths.items()}
    #     # klass = type('Path', (str, Path_2), rel_paths)
    #     klass = type('Path_2', (Path_2,), rel_paths)
    #     return str.__new__(cls, cls.join_paths(*args))
    #     return klass(paths)

    def __add__(self, other):
        paths = (self, other)
        return create_path_2(paths)
        # return create_path_descriptor(paths, self.__class__.__dict__)

    def __radd__(self, other):
        paths = (other, self)
        # return create_path_descriptor(paths, self.__dict__)
        # return create_path_descriptor(paths, self.__class__.__dict__)
        return create_path_2(paths)

    # установить
    def __setattr__(self, key, value):
        print('set_attr: ', key, value)

        # если подпуть новый, добавить
        # if key not in self.__dict__:
        if hasattr(self, '_parent'):
            setattr(self._parent.__class__, key, create_path_2([value]))
        elif key not in self.__class__.__dict__:
            # self.__class__.key = create_path_descriptor(value)
            setattr(self.__class__, key, create_path_2([value]))
        else:
            super(PathDescriptor, self).__setattr__(key, value)

    # переустановить
    def __set__(self, instance, value):
        print('re-set: ', instance, value)
        # self.path = PathDescriptor_2(value)
        self.__dict__['path'] = create_path_2([value])

    # взять
    def __get__(self, instance, owner):
        # path = instance + self
        # return instance + self
        # print('dict', self.__class__.__dict__)
        return create_path_2([instance, self], parent=self)

    @staticmethod
    def join_paths(paths):
        # чтобы при объединении путей-строк не сработала переопределенная конкатенация строк,
        # конвертируем все пути в строки
        print(paths)
        paths = map(str, paths)
        norm_path = os.path.normpath(os.path.join(*paths))
        # заменяем слеши специально для Винды
        return norm_path.replace('\\', '/')


# 3rd variant - Path and Descriptor
def create_path_3(paths, rel_paths):
    rel_paths = {key: Descriptor_3(value) for key, value in rel_paths.items()}
    # klass = type('Path', (str, Path_2), rel_paths)
    klass = type('Path_2', (Path_3,), rel_paths)
    return klass(paths)


class Path_3(str):
    # def __new__(cls, *args, **kwargs):
    #     # объединяем параметры методом path_join
    #     kwargs = {key, Descriptor()}
    #     klass = type('Path', (str,), {})
    #     return klass()
    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, cls.join_paths(*args))

    def __add__(self, other):
        paths = (self, other)
        return create_path_3(paths, self.__dict__)

    def __radd__(self, other):
        paths = (other, self)
        return create_path_3(paths, self.__dict__)

    @staticmethod
    def path_join(*paths):
        # чтобы при объединении путей-строк не сработала переопределенная конкатенация строк,
        # конвертируем все пути в строки
        paths = map(str, paths)
        norm_path = os.path.normpath(os.path.join(*paths))
        # заменяем слеши специально для Винды
        return norm_path.replace('\\', '/')


class Descriptor_3(object):
    def __init__(self, value):
        print('init ', value)
        # self.path = Path_3(value)
        # self.__dict__['path'] = Path_3(value)
        # self.sub_paths = {}

    def __set__(self, instance, value):
        print('set: ', value)
        # self.path = Path_2(value)
        self.path = create_path_3(value, rel_paths)

    def __get__(self, instance, owner):
        print('get', instance)
        # return owner + self.path
        return 'GET'

    def __setattr__(self, key, value):
        # если подпуть новый, добавить
        if key not in self.__dict__:
            self.__dict__[key] = Descriptor_3(value)
        # если это изменение старого, то вызываем сручную
        # elif key in self.__dict__:
        #     self.__dict__[key].__set__(self, type(self))


# copy of 1st variant. for experiments
class Path_ex(unicode):
    """File system path"""

    def __new__(cls, *paths, **kwargs):
        # объединяем параметры (str или Path) функцией join_paths
        return super(Path, cls).__new__(cls, join_paths(paths))

    def __init__(self, *paths, **kwargs):
        super(Path, self).__init__(*paths, **kwargs)

        self.__dict__['attrs'] = dict()

        children = kwargs.get('children', {})

        # если потомком, которых надо "унаследовать" не передали, то по возможности берем потомков последнего аргумента
        if 'children' not in kwargs:
            if len(paths) > 0:
                if hasattr(paths[-1], 'attrs'):
                    children = paths[-1].attrs
        # добавляем потомков
        self.attrs.update(children)
        self.__dict__['parent'] = kwargs.get('parent', None)

    def __add__(self, other):
        return Path(self, other)

    # todo может стоить удалить метод? тогда поведение сведется к поведению обычной строки
    def __radd__(self, other):
        return Path(other, self)

    # a_b = a.b    =>    a_b = Path(a, b, parent=b)
    # then if: a_b.c = 'more'    =>    b.c = 'more'
    def __getattr__(self, key):
        child = self.attrs[key]
        return Path(self, child, parent=child)

    def __setattr__(self, child_key, value):
        # если надо "переписать" потомка (а он может быть "в середине" и иметь потомков),
        # то передаем его потомков в новый Path в качестве потомков
        if child_key in self.attrs:
            grandchildren = self.attrs[child_key].attrs
            child = Path(value, children=grandchildren)
        else:
            child = Path(value)

        self.attrs[child_key] = child

        # если мы знаем своего настоящего отца, то создаем потомка и ему)
        if self.parent:
            self.parent.attrs[child_key] = child


    # добавляем функции из os.path в качестве методов
    isdir = os.path.isdir
    isfile = os.path.isfile

    def dirname(self):
        return Path(os.path.dirname(self))

    # не доделано, нельзя использовать
    # обход дерева путей
    # def as_dict(self, key):
    #     paths = {}
    #     for sub_key, sub_path in self._children.items():
    #         new_key = key + '.' + sub_key
    #         print('new_key', new_key, self, sub_path, self + sub_path)
    #         paths[new_key] = self + sub_path
    #
    #         if sub_path._children:
    #             paths.update(self.as_dict(new_key))
    #     return paths
