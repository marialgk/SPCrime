# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 13:59:14 2024

@author: maria
"""

# Standard libraries
from unidecode import unidecode
from difflib import get_close_matches
from importlib import resources

# Matrices and dataframes
import pandas as pd
import numpy as np


#%% PART 1 - RETRIEVE PATIENT'S ADRESS: CHECK CEP


def check_cep(series,
              zip_code_col = 'zip_code',
              start=[0, 1],
              autocorrect=False):
    """
    Brazilian zip code has 8 digits and the first digit indicates region.
    - First digit is 1: São Paulo state.
    - First digit is 0: São Paulo city.
    https://www.correios.com.br/enviar/precisa-de-ajuda/tudo-sobre-cep
    """
    ID = series.name
    
    if pd.notna(series[ zip_code_col]):
        cep = str(int(series[ zip_code_col]))
    else:
        print(f'No CEP for patient {ID}')
        return np.nan, np.nan

    dig_num = len(cep)
    if dig_num != 8:
        print(f'incorrect number of digits for patient {ID}: {cep}')
        wrong_dig_num = True
    else:
        wrong_dig_num = False

    if cep[0] not in start:
        print(f'incorrect first digit for patient {ID}: {cep}')
        wrong_1st_dig = True
    else:
        wrong_1st_dig = True

    if (wrong_dig_num == False) & (wrong_1st_dig == False):
        something_wrong = False
    else:
        something_wrong = True
        if (dig_num == 7) & (type(autocorrect) == int):
            cep = str(autocorrect) + cep
            something_wrong = "Corrected"
            print(f'autocorrected CEP for patient {ID}. New cep: {cep}')

    return cep, something_wrong


#%% PART 1 - RETRIEVE PATIENT'S ADRESS: PREPARE CEP TABLE (FROM SOURCE)
# Source: https://www.cepaberto.com/downloads/new


def build_cepDB():
    """
    Concatanates the tables from CEP Aberto database and add city names.
    """
    for i in [1, 2, 3, 4, 5]:
        csv_filename = f'sp.cepaberto_parte_{i}.csv'
        
        # Open the CSV file using importlib.resources
        with resources.open_text('SPCrime.data.cep', csv_filename) as f:
            cep_file = pd.read_csv(f,
                                   index_col=0,
                                   names=['rua', 'cep_info', 'bairro',
                                          'cidade', 'estado'],
                                   dtype=str)
        if i == 1:
            CEP = cep_file.copy()
        else:
            CEP= pd.concat([CEP, cep_file])
    
    # Na tabela de ceps, as cidades estão representadas por números.
    with resources.open_text('SPCrime.data.cep', 'cities.csv') as f:
        cities = pd.read_csv(f,
                             index_col='id',
                             usecols=[0, 1],
                             names=['id', 'cidade'],
                             dtype=str)
    cities = cities.T.to_dict(orient='list')
    
    CEP['cidade'] = pd.to_numeric(CEP['cidade']).replace(cities)
    CEP['cidade'] = CEP['cidade'].astype(str)
    
    return CEP


#%% PART 1 - RETRIEVE PATIENT'S ADRESS: CEP TO STREET AND NEIGHBOURHOOD


def cep2neighbourhood(df, zip_code_col, CEP):
    """
    Inputs:
        df = Table with postal code data on the column named by the 
             zip_code_col argument
        CEP = database built by the build_cepDB() function.
    """
    right_adress = pd.merge(df,
                            CEP,
                            left_on=zip_code_col,
                            right_index=True,
                            how='left')
    
    right_adress = right_adress.rename(columns={'rua':'street',
                                                'bairro':'neighbourhood',
                                                'cidade':'city',
                                                'estado':'state'})
    return right_adress

#%% PART 1 - RETRIEVE PATIENT'S ADRESS: NORMALIZE NEIGHBOURHOOD


def replace_abb(neighbourhood):
    """
    Replace abbreviations that hinder posterior database integration.
    """
    # Jardim
    if neighbourhood.startswith('j '):
        neighbourhood = neighbourhood.replace('j ', 'jardim ')

    # Vila
    neighbourhood = neighbourhood.replace('vl. ', 'vila ')
    if neighbourhood.startswith('vl '):
        neighbourhood = neighbourhood.replace('vl ', 'vila ')

    return neighbourhood


def norm_hood(name, abbreviation=False):
    """
    Removes trailing and leading white space, remove diacritics, 
    replace uppercase by lowercase.
    """
    if pd.isna(name):
        return np.nan
    # Remove accents
    name = unidecode(str(name))
    # Lower case
    name = name.lower()
    # Remove leading and trailing whitespace
    name = name.strip()

    # Remove abbreviations and put them as longform
    if abbreviation == True:
        name = replace_abb(name)

    return name


#%% PART 1 - RETRIEVE PATIENT'S ADRESS: MATCH SÃO PAULO DISTRICTS
# São Paulo has 96 official districts.
# Each district comprises a varying number of neighbourhoods.
# I made a table based on the website https://www.saopaulobairros.com.br/.


def open_dist_dict():
    """
    Loads database of neighbourhoods --> district. 
    """
    with resources.open_text('SPCrime.data', 'districts.tsv') as f:
        dist = pd.read_csv(f, sep='\t', dtype=str)
    dist = dist.set_index('Unnamed: 0')
    
    # Create a simplified neighbourhood > district table.
    dist_dict = dist[['district', 'neighbourhood']]
    dist_dict = dist_dict.drop_duplicates(subset='neighbourhood', keep='first')
    
    return dist_dict


def neighbourhood2dist(df, dist_dict):
    """
   Inputs:
       df = Table with postal code data on the column neighbourhood'.
       dist_dict = dictionary opened by the the open_dist_dict() function.
        
    """
    
    try:
        df_dist = pd.merge(df,
                           dist_dict,
                           left_on='neighbourhood',
                           right_on='neighbourhood',
                           how='left')
    except ValueError:
        print('This error happens when we found no valid postal code.')
        print('Check if your codes are from SP State (start with 0 or 1)')
        print('Try to turn on the option autocorrect!')
        raise
    
    df_dist.loc[df_dist['city'] != 'São Paulo', 'district'] = np.nan
    
    return df_dist


###############################################################################
###############################################################################
#%% PART 2 - CRIMINAL DATA: LOAD DATA
# Dados de 2022: https://www.ssp.sp.gov.br/estatistica/consultas


def open_crime_file(file):
    """
    Opens the SSP crime database. 
    """
    crime_S1 = pd.read_excel(file,
                             header=0,
                             sheet_name=0)
    crime_S2 = pd.read_excel(file,
                             header=0,
                             sheet_name=1)

    crime = pd.concat([crime_S1,crime_S2],
                  axis=0)
    
    crime = crime[['CIDADE', 'BAIRRO', 'NATUREZA_APURADA']]
    return crime


#%% PART 2 - CRIMINAL DATA: STANDARDIZE NAMES


def norm_city(name):
    """
    Standardize city names to aid the database merging.
    """
    if pd.isna(name):
        return np.nan

    # Remove abbreviations and put them as longform
    # This gives errors because s. can stand for "sao", "santo" and "santa".
    # But I kept like this and used close match later. It worked.
    name = name.replace('S.', 'sao ')
    name = name.replace(' (SP)', '')
    # Remove accents
    name = unidecode(str(name))
    # Lower case
    name = name.lower()
    # Remove leading and trailing whitespace
    name = name.strip()

    # There are four towns that are also the name of a São Paulo City district.
    # Here I identify them as separate cities.
    # They don't appear in my dataset, but in case we need it in the future.
    if name in ['jose bonifacio', 'pedreira', 'socorro', 'tremembe']:
        name = f'{name} (cidade)'

    return name


def standardize_crime(crime):
    crime['BAIRRO'] = crime['BAIRRO'].apply(norm_hood, abbreviation = True)
    crime['BAIRRO'] = crime['BAIRRO'].replace('centro historico de sao paulo', 'centro')
    
    crime['CIDADE'] = crime['CIDADE'].apply(norm_city)
    return crime

#%% PART 2 - CRIMINAL DATA: NEIGHBOURHOOD --> DISTRICT


def find_closest_district(hood, district_dict):
    '''
    hood = string with neighbourhood name
    district_dict = dictionary neighbourhood--> district
    '''
    if pd.isna(hood):
        print('NA value')
        return np.nan
    try:
        district = district_dict[hood]
        print('exact match')
    except KeyError:
        best_match = get_close_matches(hood, list(district_dict.keys()), n=1)
        try:
            district = district_dict[best_match[0]]
            print('close match')
        except IndexError:
            district = np.nan
            print(f'Neighbourhood not found: {hood}')
    return district


def city_sp_districts(series, district_dict):
    """
    I only have district data for São Paulo.
    So if not São Paulo City, consider the whole town as its district.

    It works only if you have applied norm_city().
    """
    if series['CIDADE'] == 'sao paulo':
        district = find_closest_district(series['BAIRRO'], district_dict)
    else:
        print('not São Paulo')
        district = series['CIDADE']

    series['LOCATION'] = district
    return series


def build_crimeDB(file,
                  districts=None):
    """
    Returns a database with all the crimes that were registered in São Paulo
    state in a given year, and where they occured.
    Input:
        crime_db = Year to calculate crime rates.
        dist_dict = dictionary opened by the the open_dist_dict() function.
    """
    if districts == None:
        districts = open_dist_dict()
    districts['district'] = districts['district'].apply(norm_hood)
    dist_dict = districts.set_index('neighbourhood')['district'].to_dict()
    
    crime = open_crime_file(file)
    crime = standardize_crime(crime)
    crime = crime.apply(city_sp_districts,
                        district_dict=dist_dict,
                        axis=1)
    return crime

#%% PART 2 - CRIMINAL DATA: ABSOLUTE CRIMINAL FREQUENCY BY DISTRICT

# Vou contar duas categorias de crime:
    # Roubos/furtos
    # Crimes violentos intencionais.

# Crimes violentos letais intencionais:
    # Homicídios dolosos,
    # Latrocínio,
    # Lesão corporal seguida de morte.
# Crimes violentos não-letais intencionais:
    # Estupro (incluí o de vulnerável), 
    # Lesão corporal dolosa,
    # Tentativa de homicídio.

# Definições de crimes violentos descritos pela SSP de Goiás:
# https://www.seguranca.go.gov.br/wp-content/uploads/2019/04/portaria-n-0236-19-ssp-de-auditoria-abril-2019-2.pdf


def filter_crime_type(crime, crime_type):
    """
    Input:
        crime = database created by the build_crimeDB() function.
        crime_type:
            'ESTUPRO'
            'FURTO - OUTROS',
            'FURTO DE VEÍCULO',
            'HOMICÍDIO DOLOSO',
            'LESÃO CORPORAL CULPOSA POR ACIDENTE DE TRÂNSITO',
            'LESÃO CORPORAL DOLOSA',
            'ROUBO - OUTROS',
            'ROUBO DE CARGA',
            'ROUBO DE VEÍCULO',
            'TENTATIVA DE HOMICIDIO',
            'TRAFICO DE ENTORPECENTES',
            'LESÃO CORPORAL CULPOSA – OUTRAS',
            'ESTUPRO DE VULNERÁVEL',
            'FURTO DE CARGA',
            'HOMICIDIO CULPOSO POR ACIDENTE DE TRANSITO',
            'EXTORSÃO MEDIANTE SEQUESTRO',
            'LATROCÍNIO',
            'LESÃO CORPORAL SEGUIDA DE MORTE',
            'HOMICIDIO CULPOSO OUTROS',
            'ROUBO A BANCO',
            'HOMICÍDIO DOLOSO POR ACIDENTE DE TRÂNSITO'
            
            'THEFT' (includes 'FURTO - OUTROS', 'FURTO DE CARGA',
                     'FURTO DE VEÍCULO', 'LATROCÍNIO', 'ROUBO - OUTROS',
                     'ROUBO A BANCO', 'ROUBO DE CARGA', 'ROUBO DE VEÍCULO')
            
            'CVLI' (Violent intentional lethal crimes:
                    'HOMICIDIO CULPOSO OUTROS', 
                    'HOMICIDIO CULPOSO POR ACIDENTE DE TRANSITO',
                    'LATROCÍNIO', 'LESÃO CORPORAL SEGUIDA DE MORTE'),

            'CVNLI' (Violent intentional non-lethal crimes:
                     'ESTUPRO', 'ESTUPRO DE VULNERÁVEL',
                     'LESÃO CORPORAL DOLOSA','TENTATIVA DE HOMICIDIO'),
                
           'CVI' (violent intentional crimes)
    """
    cat = {'THEFT' : ['FURTO - OUTROS', 'FURTO DE CARGA',
                      'FURTO DE VEÍCULO', 'LATROCÍNIO', 'ROUBO - OUTROS',
                      'ROUBO A BANCO', 'ROUBO DE CARGA', 'ROUBO DE VEÍCULO'],

    'CVLI' : ['HOMICIDIO CULPOSO OUTROS', 
              'HOMICIDIO CULPOSO POR ACIDENTE DE TRANSITO',
              'LATROCÍNIO', 'LESÃO CORPORAL SEGUIDA DE MORTE'],

    'CVNLI' : ['ESTUPRO', 'ESTUPRO DE VULNERÁVEL', 'LESÃO CORPORAL DOLOSA',
              'TENTATIVA DE HOMICIDIO'],

    'CVI' : ['ESTUPRO', 'ESTUPRO DE VULNERÁVEL', 'HOMICIDIO CULPOSO OUTROS',
             'HOMICIDIO CULPOSO POR ACIDENTE DE TRANSITO', 'LATROCÍNIO', 
             'LESÃO CORPORAL DOLOSA', 'LESÃO CORPORAL SEGUIDA DE MORTE',
             'TENTATIVA DE HOMICIDIO']}

    # crime[crime_type] = np.nan
    
    if crime_type in cat.keys():
        crime = crime['NATUREZA_APURADA'].isin(cat[crime_type])
    else:
        crime = crime[crime['NATUREZA_APURADA'] == crime_type]
 
    crime_freq = crime.groupby('LOCATION')['NATUREZA_APURADA'].count()
    
    return crime_freq

#%% PART 2 - CRIMINAL DATA: RELATIVE CRIMINAL FREQUENCY BY DISTRICT

# Prepare city population data
# Source: https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html?edicao=37225&t=resultados


def prepare_pop_data():
    """
    Prepare population data for calculating the per capita rate.
    """
    with resources.open_binary('SPCrime.data.pop', 'state.xlsx') as f:
        pop_cities = pd.read_excel(f,
                                   sheet_name='Tabela',
                                   header=0,
                                   usecols=['Unidade da Federação e Município',
                                            'População residente (Pessoas)'])

    new_names = {'Unidade da Federação e Município':'CITY',
                 'População residente (Pessoas)':'population'}
    pop_cities = pop_cities.rename(columns=new_names)
    pop_cities['CITY'] = pop_cities['CITY'].apply(norm_city)
    pop_cities = pop_cities.set_index('CITY').drop('sao paulo')

    # Prepare district population data
    # Source: https://www.nossasaopaulo.org.br/campanhas/#13
    with resources.open_binary('SPCrime.data.pop', 'district.xlsx') as f:
        pop_dist = pd.read_excel(f,
                                 header=0)
    pop_dist = pop_dist.rename(columns={'DISTRITO': 'district',
                                        'População total': 'population'})
    pop_dist['district'] = pop_dist['district'].apply(norm_hood)
    # I multiply by 1000 due to a formatting error with ',' or '.' as decimal.
    pop_dist['population'] = pop_dist['population'] * 1000
    pop_dist = pop_dist.set_index('district')

    # Put them all together
    pop = pd.concat([pop_cities, pop_dist])
    
    return pop


def rate_calc(series, var_name, pop, n=10000):
    """Calculate per capita rate of a single Pandas Series"""
    try:
        population = pop.loc[series.name]
    except KeyError:
        best_match = get_close_matches(series.name, list(pop.index), n=1)
        try:
            population = pop.loc[best_match[0]]
            print(f'close match: {series.name}')
        except IndexError:
            return np.nan
            print(f'Unavailable population for city {series.name}')
    absolute = series[var_name]
    rate = n * (absolute / population)
    return rate

###############################################################################
###############################################################################
#%% PART 3: ADD CRIMINAL DATA TO MY DATASET


def prepare_patientDB(df, crimetype):
    """Standardize patient database location names"""
    df['district'] = df['district'].apply(norm_hood)
    df['city'    ] = df['city'    ].apply(norm_city)
    
    df[f'{crimetype}_rate'] = np.nan
    return df


def add_crime_data(series, crime_rates, crimetype):
    city = series['city']
    dist = series['district']
    col_name = f'{crimetype}_rate'
    if city == 'sao paulo':
        key = dist
    else:
        key = city
    try:
        series[col_name] = crime_rates.loc[key, col_name]
    except KeyError:
        series[col_name] = np.nan
    return series

###############################################################################
###############################################################################


def mapCEP(df,
           zip_code_col,
           cep_path=np.nan,
           autocorrect=False):

    df[['zip_code_correct', 'wrong_zip']] = df.apply(check_cep,
                                                     zip_code_col=zip_code_col,
                                                     autocorrect=autocorrect,
                                                     axis=1,
                                                     result_type='expand')
    if pd.isna(cep_path):   
        CEP = build_cepDB()
        CEP.to_csv('CEP_table_compiled.tsv', sep='\t')
    else:
        CEP = pd.read_csv(cep_path, sep='\t', dtype=str)
        CEP = CEP.set_index('Unnamed: 0')
    
    df = cep2neighbourhood(df, 'zip_code_correct', CEP)
    df['neighbourhood'] = df['neighbourhood'].apply(norm_hood)
    districts = open_dist_dict()
    df= neighbourhood2dist(df, districts)
    
    return districts, df


def single_crime_rates(crime_type,
                       crime_db,
                       districts=None,
                       n_percapita=10000,
                       premade=False,
                       save_excel=False):

    if premade == False:
        crime = build_crimeDB(crime_db, districts=districts)
        crime.to_csv(f'{crime_db}_crimes.tsv', sep='\t')
    else:
        crime = pd.read_csv(crime_db, sep='\t')
        crime = crime.set_index('Unnamed: 0')
    
    crime_freq = filter_crime_type(crime, crime_type)
    
    pop = prepare_pop_data()
    
    crime_fq_rt = pd.DataFrame([crime_freq]).T
    crime_fq_rt[f'{crime_type}_rate'] = crime_fq_rt.apply(rate_calc,
                                                          var_name=crime_type,
                                                          pop=pop,
                                                          n=n_percapita,
                                                          axis=1)
    if save_excel == True:
        crime_fq_rt.to_excel(f'{crime_type}_{crime_db}.xlsx')
    return crime_fq_rt


def multiple_crime_rates(crime_types,
                         crime_db,
                         districts=None,
                         n_percapita=10000,
                         premade=False,
                         save_excel=False):
        
    if premade == False:
        crime = build_crimeDB(crime_db, districts=districts)
        crime.to_csv(f'{crime_db}_crimes.tsv', sep='\t')
        crime_db = f'{crime_db}_crimes.tsv'
        
    crimes = {}
    for i in crime_types:
        crimes[i] = single_crime_rates(i,
                                       crime_db,
                                       districts=districts,
                                       n_percapita=n_percapita,
                                       save_excel=False,
                                       premade=True)
    crime_table = pd.DataFrame.from_dict(crimes)

    if save_excel == True:
        crime_table.to_excel('crimes_SP.xlsx')

    return crime_table

def CEP2crime(df, crimetype, crime_rates):
    df = prepare_patientDB(df, crimetype)
    
    for i in crimetype:
        df = df.apply(add_crime_data,
                      crime_rates=crime_rates,
                      crimetype=i,
                      axis=1)
    return df
                
def SPCrime(df,
            zip_code_col,
            crime_type,
            crime_db,
            output_name,
            cep_path=None,
            autocorrect=False,
            premade_crime_db=False,
            n_percapita=10000,
            save_excel=True):

    districts, df_code = mapCEP(df, zip_code_col, cep_path, autocorrect)
    
    if len(crime_type) == 1:
        crime_freq = single_crime_rates(crime_type,
                                        crime_db,
                                        districts=districts,
                                        n_percapita=n_percapita,
                                        premade=premade_crime_db,
                                        save_excel=save_excel)
    else:
        crime_freq = multiple_crime_rates(crime_type,
                                          crime_db,
                                          districts=districts,
                                          n_percapita=n_percapita,
                                          premade=premade_crime_db,
                                          save_excel=save_excel)
        
    df_code_crime = CEP2crime(df_code, crime_type, crime_freq)

    df_code_crime.to_csv(f'{output_name}.tsv', sep='\t')
    
    return df_code_crime
