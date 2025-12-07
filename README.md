## Software context

This software builds upon the implementation originally developed to perform the analysis described in the paper **“Homofilia e Assimetria na Rede de Coautoria de Proposições de Lei do Congresso Brasileiro”**, available at: https://sol.sbc.org.br/index.php/brasnam/article/view/6544

The original project studied the coauthorship relations among deputies in the Brazilian Chamber of Deputies, with emphasis on homophily and asymmetry patterns in legislative collaborations. The present repository keeps the same analytical foundation, while **extending and updating the code** to support new use cases, additional years and legislatures, and a broader exploratory framework.

The original software architecture, data extraction logic and network model were created by **Lucas L. Rolim (2019)**. This repository **reuses, adapts and expands** significant parts of that code, and all credit for the original design, ideas and methodology is attributed to the original author. The extensions made here focus on:

- generalization to multiple years and legislatures  
- reproducibility and easier configuration  
- automation of the mining and network-building process  
- incorporation of a command line interface (CLI) to run the pipeline

**Abstract of the original paper:**

> The Chamber of Deputies is the maximum degree of people representativity in Brazil, having as one of its main goals the approval of law and projects to develop and manage the country. We have deputies from different regions, parties, sex, ethnicity, and education levels occupying the 513 existing chairs and creating alliances and negotiations to approve their projects in this heterogeneous environment. The goal of this work is to describe the coauthorship network among these deputies, concentrating in identify and characterize homophily and asymmetry patterns. We will propose and evaluate a new methodology to analyze the homophily in the congress network. Using the proposed methodology we will identify important aspects, as a high level of asymmetry and a lack of homophily among minorities.

---

## Functionalities

The software implements the following main functionalities (from the original project):

- extraction of data about coauthorship in the Brazilian Chamber of Deputies from public sources  
- methods to apply Social Network Analysis (SNA), including homophily and asymmetry  
- original metrics to measure homophily in weighted networks  

The present version **extends** these functionalities, adding in particular:

- support for **multiple years and multiple legislatures** in a single run  
- improved organization of data and extraction routines  
- automatic generation and naming of network files (including years and legislature in the filename)  
- a command line interface to run the different miners and to build the networks  
- auxiliary scripts for:
  - distribution of number of authors per proposal  
  - identification of proposals with unusually high numbers of coauthors  
  - exploratory inspection of networks in different years  

---

## Utilização do Software

A utilização e a motivação originais encontram-se descritas no artigo **“Homofilia e Assimetria na Rede de Coautoria de Proposições de Lei do Congresso Brasileiro”**, publicado no BraSNAM (Brazilian Workshop on Social Network Analysis and Mining).

Este repositório representa uma **continuidade** desse trabalho. A arquitetura básica e diversos componentes foram desenvolvidos por **Lucas L. Rolim**, e foram aqui reorganizados e expandidos para novos propósitos analíticos. O presente repositório mantém o devido crédito ao autor original e às ideias apresentadas no artigo, ao mesmo tempo em que amplia o escopo de análise e facilita a utilização do software em cenários adicionais, como:

- análise de legislaturas mais recentes  
- comparação entre diferentes períodos  
- geração de redes de coautoria para conjuntos de anos específicos  

---


