__all__ = ('ModelLink', 'Field',)

from scarletio import RichAttributeErrorBaseType, to_coroutine, Task, shield
from hata import KOKORO

COMPILATION_FILE_NAME = '<model_linker>'
SLOT_NAME_PREFIX = '_slot_'
DISPLAY_DEFAULT_PREFIX = 'DEFAULT_'
ENTRY_ID_NOT_LOADED = -1
ENTRY_ID_MISSING = -2


class CodeBuilder(RichAttributeErrorBaseType):
    __slots__ = ('indent', 'parts')
    
    def __new__(cls):
        self = object.__new__(cls)
        self.indent = 0
        self.parts = []
        return self
    
    def __call__(self, *parts_to_add):
        self.add_line(*parts_to_add)
        return self
    
    def __enter__(self):
        self.indent += 1
        return self
    
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.indent -= 1
        return False
    
    
    def build(self):
        return ''.join(self.parts)
    
    
    def add(self, *parts_to_add):
        if parts_to_add:
            self._maybe_add_indent()
            self.parts.extend(parts_to_add)
    
    
    def add_line(self, *parts_to_add):
        if parts_to_add:
            self._maybe_add_indent()
            parts = self.parts
            parts.extend(parts_to_add)
            parts.append('\n')
    
    
    def add_line_break(self):
        self.parts.append('\n')
    
    
    def _maybe_add_indent(self):
        parts = self.parts
        if (not parts) or (parts[-1] == '\n'):
            parts.append('    ' * self.indent)


class Field(RichAttributeErrorBaseType):
    __slots__ = ('field', 'default', 'primary_key', 'query_key')
    
    def __new__(cls, field, default = None, *, primary_key = False, query_key = None):
        self = object.__new__(cls)
        self.field = field
        self.default = default
        self.primary_key = primary_key
        self.query_key = query_key
        return self
    
    
    def __get__(self, instance, type_):
        raise NotImplementedError()
    
    def __set__(self, instance, value):
        raise NotImplementedError()


def compile_and_get(variable_name, code, globals=None):
    if globals is None:
        globals = {}
    
    locals_ = {}
    
    exec(compile(code, COMPILATION_FILE_NAME, 'exec', optimize = 2), globals, locals_)
    
    return locals_[variable_name]


def compile_getter(attribute_name, slot_name, require_internal_field):
    func_name = f'_get_{attribute_name}'
    
    code = CodeBuilder()
    
    with code('def ', func_name, '(self):'):
        if require_internal_field:
            code('return self.', slot_name)
        else:
            code('return self.', attribute_name)
    
    return compile_and_get(func_name, code.build())



def compile_setter(attribute_name, slot_name, require_internal_field):
    func_name = f'_set_{attribute_name}'
    
    code = CodeBuilder()
    
    with code('def ', func_name, '(self, value, field):'):
        if require_internal_field:
            code('self.', slot_name, ' = value')
            code('self._field_modified(field)')
        else:
            code('self.', attribute_name, ' = value')
    
    return compile_and_get(func_name, code.build())



def get_new_method_string(fields, globals, added_initializer):
    
    code = CodeBuilder()
    code.add_line()
    
    with code('def __new__(cls, parent):'):
        if added_initializer is None:
            code('self = ModelLink.__new__(cls, parent)')
        else:
            code('self = INITIALIZER(cls, parent)')
        
        for field in fields:
            if (field.query_key is not None) and (added_initializer is not None):
                continue
            
            if field.primary_key:
                display_default = repr(ENTRY_ID_NOT_LOADED)
            
            else:
                default = field.default
                if default is None or isinstance(default, (int, float, str)):
                    display_default = repr(default)
                
                else:
                    display_default = 'DEFAULT_' + field.field_name.upper()
                    globals[display_default] = default
                    
                    if callable(default):
                        display_default = display_default + '()'
            
            
            if field.is_require_internal_field():
                attribute_name = field.slot_name
            else:
                attribute_name = field.attribute_name
            
            code('self.', attribute_name, ' = ', display_default)
        
        code('return self')
    
    return code.build()


def _get_primary_key_field(fields):
    for field in fields:
        if field.primary_key:
            return field
    
    raise RuntimeError('Missing primary key field.')


def _get_query_key_field(fields):
    for field in fields:
        if field.query_key is not None:
            return field
    
    raise RuntimeError('Missing query key field.')


def get_save_method_string(fields, engine):
    primary_key_field = _get_primary_key_field(fields)
    
    code = CodeBuilder()
    
    with code('async def __save__(self):'):
        if (engine is None):
            code.add_line('pass')
        
        else:
            with code('try:'):
                with code('async with ENGINE.connect() as connector:'):
                    with code('while True:'):
                        code('fields_modified = self._fields_modified')
                        with code('if (fields_modified is None):'):
                            code('break')
                        
                        code('self._fields_modified = None')
                        
                        code('entry_id = self.', primary_key_field.attribute_name)
                        with code('if entry_id > 0:'):
                            with code('await connector.execute('):
                                with code('TABLE.update('):
                                    code('MODEL.', primary_key_field.field_name, ' == self.entry_id,')
                                
                                with code(').values('):
                                    code('**{field.field_name: field.getter(self) for field in fields_modified}')
                                
                                code(')')
                            code(')')
                            code('continue')
                        
                        with code('if entry_id == ', str(ENTRY_ID_MISSING), ':'):
                            with code('response = await connector.execute('):
                                with code('TABLE.insert().values('):
                                    for field in fields:
                                        if not field.primary_key:
                                            if field.query_key is None:
                                                attribute_name = field.slot_name
                                            else:
                                                attribute_name = field.attribute_name
                                            code(field.field_name, ' = self.', attribute_name, ',')
                                        
                                with code(').returning('):
                                    code('MODEL.', primary_key_field.field_name, ',')
                                
                                code(')')
                            code(')')
                            
                            code('result = await response.fetchone()')
                            code('self.', primary_key_field.attribute_name, ' = result[0]')
                            code('continue')
                        
                        code('return')
            
            with code('finally:'):
                code('self._saving = False')
    
    return code.build()


def get_loaded_method_string(fields, engine):
    primary_key_field = _get_primary_key_field(fields)
    
    code = CodeBuilder()
    with code('def __loaded__(self):'):
        code('return self.', primary_key_field.attribute_name, ' != ', repr(ENTRY_ID_NOT_LOADED))
    
    return code.build()


def get_load_method_string(fields, engine):
    query_key_field = _get_query_key_field(fields)
    primary_key_field = _get_primary_key_field(fields)
    
    code = CodeBuilder()
    with code('async def __load__(self):'):
        if engine is None:
            code('self.', primary_key_field.attribute_name, ' = ', str(ENTRY_ID_MISSING))
            code('self.__set_initial_values__()')
        
        else:
            with code('try:'):
                with code('async with ENGINE.connect() as connector:'):
                    with code('response = await connector.execute('):
                        with code('TABLE.select('):
                            code('MODEL.', query_key_field.field_name, ' == self.', query_key_field.query_key, ', ')
                        code(')')
                    code(')')
                    
                    code('result = await response.fetchone()')
                
                with code('if result is None:'):
                    code('self.', primary_key_field.attribute_name, ' = ', str(ENTRY_ID_MISSING))
                    code('self.__set_initial_values__()')
                
                with code('else:'):
                    for field in fields:
                        if (field is query_key_field):
                            continue
                        
                        if field.primary_key:
                            attribute_name = field.attribute_name
                        else:
                            attribute_name = field.slot_name
                        
                        code('self.', attribute_name, ' = result.', field.field_name)
            
            
            with code('finally:'):
                code('self._load_task = None')
    
    return code.build()


def _get_require_internal_field(primary_key, query_key):
    if primary_key:
        return False
    
    if (query_key is not None):
        return False
    
    return True


class FieldDescriptor(RichAttributeErrorBaseType):
    __slots__ = (
        'field', 'field_name', 'id', 'getter', 'setter', 'attribute_name', 'default', 'primary_key', 'query_key',
        'slot_name',
    )
    
    def __new__(cls, attribute_name, field):
        data_base_field = field.field
        
        if data_base_field is None:
            field_name = attribute_name
        else:
            field_name = data_base_field.property.key
        
        default = field.default
        primary_key = field.primary_key
        query_key = field.query_key
        slot_name = SLOT_NAME_PREFIX + attribute_name
        
        require_internal_field = _get_require_internal_field(primary_key, query_key)
        
        getter = compile_getter(attribute_name, slot_name, require_internal_field)
        setter = compile_setter(attribute_name, slot_name, require_internal_field)
        
        self = object.__new__(cls)
        
        self.field = data_base_field
        self.attribute_name = attribute_name
        self.field_name = field_name
        self.getter = getter
        self.setter = setter
        self.default = default
        self.primary_key = primary_key
        self.query_key = query_key
        self.slot_name = slot_name
        
        return self
    
    
    def __get__(self, instance, instance_type):
        if instance is None:
            return self
        
        return self.getter(instance)
    
    
    def __set__(self, instance, value):
        if instance is None:
            return
        
        self.setter(instance, value, self)
    
    
    def is_require_internal_field(self):
        return _get_require_internal_field(self.primary_key, self.query_key)


class ModelLinkType(type):
    def __new__(cls, class_name, class_parents, class_attributes, *, model, table, engine, is_base = False):
        
        if not is_base:
            collected_fields = []
            
            for class_attribute_name, class_attribute_value in class_attributes.items():
                if isinstance(class_attribute_value, Field):
                    collected_fields.append((class_attribute_name, class_attribute_value))
            
            
            fields = []
            
            for class_attribute_name, class_attribute_value in collected_fields:
                field = FieldDescriptor(class_attribute_name, class_attribute_value)
                fields.append(field)
                if field.is_require_internal_field():
                    class_attributes[class_attribute_name] = field
                else:
                    del class_attributes[class_attribute_name]
            
            fields = tuple(fields)
            class_attributes['__fields__'] = fields
            
            added_initializer = class_attributes.get('__new__', None)
            
            globals = {}
            globals['ModelLink'] = ModelLink
            if (added_initializer is not None):
                globals['INITIALIZER'] = added_initializer
            globals['ENGINE'] = engine
            globals['TABLE'] = table
            globals['MODEL'] = model

            new_method_string = get_new_method_string(fields, globals, added_initializer)
            save_method_string = get_save_method_string(fields, engine)
            loaded_method_string = get_loaded_method_string(fields, engine)
            load_method_string = get_load_method_string(fields, engine)
            
            class_attributes['__new__'] = compile_and_get('__new__', new_method_string, globals)
            class_attributes['__save__'] = compile_and_get('__save__', save_method_string, globals)
            class_attributes['__loaded__'] = compile_and_get('__loaded__', loaded_method_string, globals)
            class_attributes['__load__'] = compile_and_get('__load__', load_method_string, globals)
            
            extra_slots = tuple(
                field.slot_name if field.is_require_internal_field() else field.attribute_name for field in fields
            )
            
            added_slots = class_attributes.get('__slots__', None)
            if added_slots is None:
                new_slots = {*extra_slots, '__dict__'}
            else:
                new_slots = {*extra_slots, *added_slots}
            new_slots = tuple(new_slots)
            
            class_attributes['__slots__'] = new_slots
        
        return type.__new__(cls, class_name, class_parents, class_attributes)


class ModelLink(
    RichAttributeErrorBaseType, metaclass = ModelLinkType, model = None, table = None, engine = None, is_base = True
):
    __slots__ = ('__weakref__', '_load_task', '_fields_modified', '_saving')
    
    
    def __new__(cls, parent):
        self = object.__new__(cls)
        self._load_task = None
        self._fields_modified = None
        self._saving = False
        return self
    
    
    def __await__(self):
        if not self.__loaded__():
            yield from self.__load_synchronised__()
        
        return self
    
    
    def _field_modified(self, field):
        fields_modified = self._fields_modified
        if (fields_modified is None):
            fields_modified = set()
            self._fields_modified = fields_modified
        
        fields_modified.add(field)
    
    
    def __loaded__(self):
        return True
    
    
    def _fields_resolved(self):
        self._fields_modified = None
    
    
    @to_coroutine
    def __load_synchronised__(self):
        load_task = self._load_task
        if (load_task is None):
            load_task = Task(self.__load__(), KOKORO)
            self._load_task = load_task
        
        yield from shield(load_task, KOKORO)
    
    
    def __bool__(self):
        return self.__loaded__()
    
    
    def __set_initial_values__(self):
        self._fields_modified = None
    
    
    def __getstate__(self):
        state = {}
        
        for field in self.__fields__:
            key = field.attribute_name
                
            if field.is_require_internal_field():
                attribute_name = field.slot_name
            else:
                attribute_name = field.attribute_name
            
            value = getattr(self, attribute_name)
            
            state[key] = value
        
        return state
    
    
    def __setstate__(self, state):
        self._load_task = None
        self._fields_modified = None
        self._saving = None
        
        for field in self.__fields__:
            key = field.attribute_name
                
            if field.is_require_internal_field():
                attribute_name = field.slot_name
            else:
                attribute_name = field.attribute_name
            
            setattr(self, attribute_name, state[key])
    
    
    def save(self):
        if not self._saving:
            self._saving = True
            Task(self.__save__(), KOKORO)
