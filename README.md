# SP Crime

This simple package processes data from the São Paulo Public Security Secretariat (SSP-SP) and adds them to a table with a postal 
code (CEP) column. SPCrime was designed to add data with a Pandas DataFrame object.

As for its name, SPCrime supports only data from São Paulo State. Each Brazilian federation unit has its own
Public Security Secretariat and policies on data sharing.

# Requirements:
- Python >3.8

- Pandas
- Numpy
- Unidecode
- openpyxl

## Installation:

**Github**:
```
pip install git+https://github.com/marialgk/SPCrime.git
```

**PyPi**:

A PyPi version will be available soon.

## Use:

To import the principal function:
```
from SPCrime import SPCrime
```

Given SSP-SP data and a pandas DataFrame containing postal codes, the function SPCrime adds *per capita* crime rates in the 
location of the zip code. The user specifies the year and type of crime. The program saves a tab-separated file (TSV) of the
data frame with the new column and returns a DataFrame object.

For each year, the first run requires the processing of the corresponding SSP criminal database (it takes ~40min). Once this
database is built and saved, the user can reuse them to get faster runs.

### SPCrime(*args, **kwargs) function
#### args:
- `df` (Pandas DataFrame): Pandas DataFrame object including a column of postal codes without the hyphen. To understand the
- postal codes (CEP), refer to the [Correios website](https://www.correios.com.br/enviar/precisa-de-ajuda/tudo-sobre-cep).
- `zip_code_col` (str): Name of the DataFrame column containing the postal codes (CEP).
- `crime_db` (str): Name of the file downloaded from the "Dados Criminais" header of the page [https://www.ssp.sp.gov.br/estatistica/consultas](https://www.ssp.sp.gov.br/estatistica/consultas).
  It is the SSP-SP crime database of a whole year.
- `output_name` (str): name of the output file, which is a TSV table.
- `crime_type` (str): crime category for which the *per capita* rate will be added. The possible values, as released by SSP,
   are:
    - 'ESTUPRO'
    - 'FURTO - OUTROS',
    - 'FURTO DE VEÍCULO',
    - 'HOMICÍDIO DOLOSO',
    - 'LESÃO CORPORAL CULPOSA POR ACIDENTE DE TRÂNSITO',
    - 'LESÃO CORPORAL DOLOSA',
    - 'ROUBO - OUTROS',
    - 'ROUBO DE CARGA',
    - 'ROUBO DE VEÍCULO',
    - 'TENTATIVA DE HOMICIDIO',
    - 'TRAFICO DE ENTORPECENTES',
    - 'LESÃO CORPORAL CULPOSA – OUTRAS',
    - 'ESTUPRO DE VULNERÁVEL',
    - 'FURTO DE CARGA',
    - 'HOMICIDIO CULPOSO POR ACIDENTE DE TRANSITO',
    - 'EXTORSÃO MEDIANTE SEQUESTRO',
    - 'LATROCÍNIO',
    - 'LESÃO CORPORAL SEGUIDA DE MORTE',
    - 'HOMICIDIO CULPOSO OUTROS',
    - 'ROUBO A BANCO',
    - 'HOMICÍDIO DOLOSO POR ACIDENTE DE TRÂNSITO'
    -  **'THEFT':**: categoria que inclui 'FURTO - OUTROS', 'FURTO DE CARGA', 'FURTO DE VEÍCULO', 'LATROCÍNIO',
      'ROUBO - OUTROS', 'ROUBO A BANCO', 'ROUBO DE CARGA', 'ROUBO DE VEÍCULO'.
    - **'CVLI':** Violent intentional lethal crimes, which include 'HOMICIDIO CULPOSO OUTROS', 
     'HOMICIDIO CULPOSO POR ACIDENTE DE TRANSITO', 'LATROCÍNIO', 'LESÃO CORPORAL SEGUIDA DE MORTE'.
    - **'CVNLI':** Violent intentional non-lethal crimes, which include 'ESTUPRO', 'ESTUPRO DE VULNERÁVEL',
     'LESÃO CORPORAL DOLOSA','TENTATIVA DE HOMICIDIO'.
    - **'CVI'**: Violent intentional crimes, which include the two categories above.

#### kwargs:
- `cep_path`: None or str. Default None. If you have already built the postal code database, insert the relative
  path and file name. When the database is built, the module saves a file named "CEP_table_compiled.tsv" in the
  working directory.
- `premade_crime_db´`: Boolean. Default None. If you have already built the criminal database for a given year, insert
  the file name. When the database is built, the module saves a file named "20**_crimes.tsv" in the working directory.
  This will make your run significantly faster.
- `autocorrect`: False, 0 or 1. Default False. A valid postal code (CEP) is eight digits long. In autocorrect, if
  the code is seven-digit long, you can opt to append either 0 or 1 at the beginning of the string. According to the
  Brazilian post service (Correios), 0 stands for the SP Capital, while 1 stands for the rest of the state. We recommend
  to set the `autocorrect` option to 0 because Excel and Python interpret the CEP as numeric and remove the trailing zeros.
- `n_percapita`: int. Default 10000. The crime rate is calculated per a number of inhabitants (ex. 3 murders per 10,000 persons).

#### Outputs:

**Returns**: Pandas DataFrame with the original table and a new crime rate column.

**Saved files**:
- `{outname}.tsv`: Tab separate file with the original table and a new crime rate column.
- `20**_crimes.tsv`: Crime database in the year of 20**. Only if building the database.
-  `CEP_table_compiled.tsv`: CEP to adress database. Only if building the database.

## Citation:

A short paper describing SPCrime was submitted to the Brazilian Symposium on Bioinformatics, which will be held in December
of 2024.

**ABNT:**
> GABRIEL-KUNIYOSHI, Maria Laura; MARTINS-JUNIOR, David Correa; SIMÕES, Sérgio Nery; BRENTANI, Helena. SP crime: A tool for merging
> criminal and medical data. **Proceedings of the Brazilian Symposium on Bioinformatics**, Vitória, dez., 2024. No prelo.

**BibTex:**
```
@article{Kuniyoshi2024,
	title = {SP crime: A tool for merging criminal and medical data},
	journal = {Proceedings of the Brazilian Symposium on Bioinformatics},
	author = {Gabriel-Kuniyoshi, Maria Laura and Martins-Junior, David Correa and Simoes, Sergio Nery and Brentani, Helena},
	month = dez,
	year = {\noop{2024}in press}
}
```
