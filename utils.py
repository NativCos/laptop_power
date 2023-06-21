

class RingBuffer:
    _buffer = list()
    _head_index = 0
    _size = 0

    @property
    def size(self):
        return self._size

    def __init__(self, size):
        self._size = size
        for _ in range(size):
            self._buffer.append(None)

    def append(self, data):
        self._buffer[(self._head_index + 1) % self._size] = data
        self._head_index = (self._head_index + 1) % self._size

    def get_last(self, quantity=1):
        if quantity > self._size:
            raise ValueError()
        if self.get_by_index(quantity % self._size) is None:
            raise RuntimeError('Данные еще не готовы для среза их еще нет')
        first_part = self._head_index - quantity if self._head_index >= quantity else None
        second_part = self._size - (quantity - self._head_index) if quantity > self._head_index else self._size
        return self._buffer[self._head_index: first_part: -1] + self._buffer[self._size - 1: second_part: -1]

    def get_by_index(self,index):
        # TODO: ничего не проверял
        if self._head_index >= index:
            return self._buffer[self._head_index - index]
        else:
            return self._buffer[self._size - (index - self._head_index)]

    def fill_by_object(self, obj):
        for i in range(self._size):
            self._buffer.insert(i, obj)

