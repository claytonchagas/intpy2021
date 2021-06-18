import pickle
import hashlib
import os
import threading

from intpy.parser_params import get_params
from intpy.banco import Banco
from intpy.logger.log import debug, warn

#from . import CONEXAO_BANCO

# Opening database connection and creating select query to the database
# to populate DATA_DICTIONARY
CONEXAO_BANCO = Banco(os.path.join(".intpy", "intpy.db"))

DATA_DICTIONARY = {}

NEW_DATA_DICTIONARY = {}

argsp_v, argsp_no_cache = get_params()

def _get_file_name(id):
    return "{0}.{1}".format(id, "ipcache")

def _deserialize(id):
    try:
        with open(".intpy/cache/{0}".format(_get_file_name(id)), 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError as e:
        warn("corrupt environment. Cache reference exists for a function in database but there is no file for it in cache folder.\
Have you deleted cache folder?")
        _autofix(id)
        return None

def _populate_cached_data_dictionary():
    db_connection = Banco(os.path.join(".intpy", "intpy.db"))
    list_of_ipcache_files = db_connection.executarComandoSQLSelect("SELECT cache_file FROM CACHE")
    for ipcache_file in list_of_ipcache_files:
        ipcache_file = ipcache_file[0].replace(".ipcache", "")
        
        result = _deserialize(ipcache_file)
        if(result is None):
            continue
        else:
            with CACHED_DATA_DICTIONARY_SEMAPHORE:
                DATA_DICTIONARY[ipcache_file] = result
    db_connection.fecharConexao()

if argsp_v == ['1d-ad'] or ['v022x'] or ['2d-ad'] or ['v023x']:
    list_of_ipcache_files = CONEXAO_BANCO.executarComandoSQLSelect("SELECT cache_file FROM CACHE")
    for ipcache_file in list_of_ipcache_files:
        ipcache_file = ipcache_file[0].replace(".ipcache", "")
        result = _deserialize(ipcache_file)
        if(result is None):
            continue
        else:
            DATA_DICTIONARY[ipcache_file] = result
elif argsp_v == ['2d-ad-t'] or ['v024x']:
    CACHED_DATA_DICTIONARY_SEMAPHORE = threading.Semaphore()
    load_cached_data_dictionary_thread = threading.Thread(target=_populate_cached_data_dictionary)
    load_cached_data_dictionary_thread.start()


def _save(file_name):
    CONEXAO_BANCO.executarComandoSQLSemRetorno("INSERT OR IGNORE INTO CACHE(cache_file) VALUES ('{0}')".format(file_name))

#Versão desenvolvida por causa do _save em salvarNovosDadosBanco para a v0.2.5.x e a v0.2.6.x, com o nome da função
def _save_fun_name(file_name, fun_name):
    CONEXAO_BANCO.executarComandoSQLSemRetorno("INSERT OR IGNORE INTO CACHE(cache_file, fun_name) VALUES ('{0}', '{1}')".format(file_name, fun_name))


def _get(id):
    return CONEXAO_BANCO.executarComandoSQLSelect("SELECT cache_file FROM CACHE WHERE cache_file = '{0}'".format(id))

#Versão desenvolvida por causa do _get_fun_name, que diferente do _get, recebe o nome da função ao invés do id, serve para a v0.2.5.x e a v0.2.6.x, que tem o nome da função
def _get_fun_name(fun_name):
    return CONEXAO_BANCO.executarComandoSQLSelect("SELECT cache_file FROM CACHE WHERE fun_name = '{0}'".format(fun_name))


def _remove(id):
    CONEXAO_BANCO.executarComandoSQLSemRetorno("DELETE FROM CACHE WHERE cache_file = '{0}';".format(id))


def _get_id(fun_name, fun_args, fun_source):
    return hashlib.md5((fun_name + str(fun_args) + fun_source).encode('utf')).hexdigest()


def _get_cache_data_v021x(id):
    #Verificando se há dados salvos em DATA_DICTIONARY
    if(id in DATA_DICTIONARY):
        return DATA_DICTIONARY[id]

    list_file_name = _get(_get_file_name(id))
    file_name = None
    if(len(list_file_name) == 1):
        file_name = list_file_name[0]

    return _deserialize(id) if file_name is not None else None


def _get_cache_data_v022x(id):  
    #Checking if the result is saved in the cache
    if(id in DATA_DICTIONARY):
        return DATA_DICTIONARY[id]

    return None


def _get_cache_data_v023x(id):
    #Checking if the result is saved in the cache
    if(id in DATA_DICTIONARY):
        return DATA_DICTIONARY[id]
    
    #Checking if the result was already processed at this execution
    if(id in NEW_DATA_DICTIONARY):
        return NEW_DATA_DICTIONARY[id]

    return None


def _get_cache_data_v024x(id):
    #Checking if the result is saved in the cache
    with CACHED_DATA_DICTIONARY_SEMAPHORE:
        if(id in DATA_DICTIONARY):
            return DATA_DICTIONARY[id]

    #Checking if the result was already processed at this execution
    if(id in NEW_DATA_DICTIONARY):
        return NEW_DATA_DICTIONARY[id]

    return None


FUNCTIONS_ALREADY_SELECTED_FROM_DB = []

def _get_cache_data_v025x(id, fun_name):
    #Checking if the results of this function were already selected from
    #the database and inserted on the dictionary DATA_DICTIONARY
    if(fun_name in FUNCTIONS_ALREADY_SELECTED_FROM_DB):
        #Checking if the result is saved in the cache
        if(id in DATA_DICTIONARY):
            return DATA_DICTIONARY[id]

        #Checking if the result was already processed at this execution
        if(id in NEW_DATA_DICTIONARY):
            return NEW_DATA_DICTIONARY[id][0]

    else:
        #Creating a select query to add to DATA_DICTIONARY all data
        #related to the function fun_name
        list_file_names = _get_fun_name(fun_name)
        for file_name in list_file_names:
            file_name = file_name[0].replace(".ipcache", "")
            
            result = _deserialize(file_name)
            if(result is None):
                continue
            else:
                DATA_DICTIONARY[file_name] = result

        FUNCTIONS_ALREADY_SELECTED_FROM_DB.append(fun_name)

        ######print("DATA_DICTIONARY DEPOIS:", DATA_DICTIONARY)

        if(id in DATA_DICTIONARY):
            return DATA_DICTIONARY[id]

    return None


def add_new_data_to_CACHED_DATA_DICTIONARY(list_file_names):
    for file_name in list_file_names:
        file_name = file_name[0].replace(".ipcache", "")
        
        result = _deserialize(file_name)
        if(result is None):
            continue
        else:
            DATA_DICTIONARY[file_name] = result

    ######print("DATA_DICTIONARY DEPOIS:", DATA_DICTIONARY)

def _get_cache_data_v026x(id, fun_name):
    #Checking if the results of this function were already selected from
    #the database and inserted on the dictionary DATA_DICTIONARY
    if(fun_name in FUNCTIONS_ALREADY_SELECTED_FROM_DB):
        #Checking if the result is saved in the cache
        if(id in DATA_DICTIONARY):
            return DATA_DICTIONARY[id]

        #Checking if the result was already processed at this execution
        if(id in NEW_DATA_DICTIONARY):
            return NEW_DATA_DICTIONARY[id][0]
    
    else:
        #Creating a select query to add to DATA_DICTIONARY all data
        #related to the function fun_name
        FUNCTIONS_ALREADY_SELECTED_FROM_DB.append(fun_name)
        id_file_name = _get_file_name(id)
        
        list_file_names = _get(fun_name)
        for file_name in list_file_names:
            if(file_name[0] == id_file_name):
                thread = threading.Thread(target=add_new_data_to_CACHED_DATA_DICTIONARY, args=(list_file_names,))
                thread.start()

                file_name = file_name[0].replace(".ipcache", "")
                return _deserialize(file_name)
        
        thread = threading.Thread(target=add_new_data_to_CACHED_DATA_DICTIONARY, args=(list_file_names,))
        thread.start()

    return None


def _get_cache_data_v027x(id):
    #Checking if the result is stored in DATA_DICTIONARY
    if(id in DATA_DICTIONARY):
        return DATA_DICTIONARY[id]

    #Checking if the result is stored in NEW_DATA_DICTIONARY
    if(id in NEW_DATA_DICTIONARY):
        return NEW_DATA_DICTIONARY[id]
    
    ######print("PESQUISANDO NO BANCO...")

    #Checking if the result is on database
    list_file_name = _get(_get_file_name(id))

    if(len(list_file_name) == 1):
        result = _deserialize(id)
        
        if(result is not None):
            DATA_DICTIONARY[id] = result

            ######print("DATA_DICTIONARY DEPOIS:", DATA_DICTIONARY)
        
        return result

    return None


# Aqui misturam as versões v0.2.1.x a v0.2.7.x
def get_cache_data(fun_name, fun_args, fun_source, argsp_v):
    id = _get_id(fun_name, fun_args, fun_source)

    if argsp_v == ['1d-ow'] or ['v021x']:
        ret_get_cache_data_v021x = _get_cache_data_v021x(id)
        return ret_get_cache_data_v021x
    elif argsp_v == ['1d-ad'] or ['v022x']:
        ret_get_cache_data_v022x = _get_cache_data_v022x(id)
        return ret_get_cache_data_v022x
    elif argsp_v == ['2d-ad'] or ['v023x']:
        ret_get_cache_data_v023x = _get_cache_data_v023x(id)
        return ret_get_cache_data_v023x
    elif argsp_v == ['2d-ad-t'] or ['v024x']:
        ret_get_cache_data_v024x = _get_cache_data_v024x(id)
        return ret_get_cache_data_v024x
    elif argsp_v == ['2d-ad-f'] or ['v025x']:
        ret_get_cache_data_v025x = _get_cache_data_v025x(id, fun_name)
        return ret_get_cache_data_v025x
    elif argsp_v == ['2d-ad-ft'] or ['v026x']:
        ret_get_cache_data_v026x = _get_cache_data_v026x(id, fun_name)
        return ret_get_cache_data_v026x
    elif argsp_v == ['2d-lz'] or ['v027x']:
        ret_get_cache_data_v027x = _get_cache_data_v027x(id)
        return ret_get_cache_data_v027x


def _autofix(id):
    debug("starting autofix")
    debug("removing {0} from database".format(id))
    _remove(_get_file_name(id))
    debug("environment fixed")


# Aqui misturam as versões v0.2.1.x a v0.2.7.x
def create_entry(fun_name, fun_args, fun_return, fun_source, argsp_v):
    id = _get_id(fun_name, fun_args, fun_source)
    if argsp_v == ['1d-ow'] or ['v021x'] or ['1d-ow'] or ['v021x']:
        DATA_DICTIONARY[id] = fun_return
    elif argsp_v == ['2d-ad'] or ['v023x'] or ['2d-ad-t'] or ['v024x'] or ['2d-lz'] or ['v027x']:
        NEW_DATA_DICTIONARY[id] = fun_return
    elif  argsp_v == ['2d-ad-f'] or ['v025x'] or ['2d-ad-ft'] or ['v026x']:
        NEW_DATA_DICTIONARY[id] = (fun_return, fun_name)


# Aqui misturam as versões v0.2.1.x a v0.2.7.x
def salvarNovosDadosBanco(argsp_v):
    def _serialize(return_value, file_name):
        with open(".intpy/cache/{0}".format(_get_file_name(file_name)), 'wb') as file:
            return pickle.dump(return_value, file, protocol=pickle.HIGHEST_PROTOCOL)

    if argsp_v == ['1d-ow'] or['v021x'] or ['1d-ow'] or ['v021x']:
        for id in DATA_DICTIONARY:
            debug("serializing return value from {0}".format(id))
            _serialize(DATA_DICTIONARY[id], id)

            debug("inserting reference in database")
            _save(_get_file_name(id))
    
    elif argsp_v == ['2d-ad'] or ['v023x'] or ['2d-ad-t'] or ['v024x'] or ['2d-lz'] or ['v027x']:
        for id in NEW_DATA_DICTIONARY:
            debug("serializing return value from {0}".format(id))
            _serialize(NEW_DATA_DICTIONARY[id], id)

            debug("inserting reference in database")
            _save(_get_file_name(id))
    
    elif  argsp_v == ['2d-ad-f'] or ['v025x'] or ['2d-ad-ft'] or ['v026x']:
        for id in NEW_DATA_DICTIONARY:
            debug("serializing return value from {0}".format(id))
            _serialize(NEW_DATA_DICTIONARY[id][0], id)

            debug("inserting reference in database")
            _save_fun_name(_get_file_name(id), NEW_DATA_DICTIONARY[id][1])

    CONEXAO_BANCO.salvarAlteracoes()
    CONEXAO_BANCO.fecharConexao()
