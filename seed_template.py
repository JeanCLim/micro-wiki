import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import ArticleTemplate, Company

company = Company.objects.first()

# Evita duplicação do template na execução do script.
template, created = ArticleTemplate.objects.get_or_create(
    title='Procedimento de Geração e Envio de XML',
    company=company,
    defaults={
        'default_visibility': 'PUBLIC',
    }
)

# Define tags via TaggableManager (M2M) após salvar o objeto.
# template.default_tags.add('xml', 'envio', 'contador', 'fechamento')


html_content = """
<h2>1. Verificação Inicial de Servidores (TSD)</h2>
<p>
  <strong>Atenção:</strong> A primeira coisa a ser feita é descobrir se o computador que o usuário enviou possui mais de uma TSD instalada. Se tiver, você <strong>deve priorizar a TSD que o cliente informar</strong>.
</p>

<h2>2. Criação da Pasta de Destino</h2>
<p>
  Após definir a TSD correta, você deve criar a pasta onde os arquivos XML serão salvos, antes de ir no host gerar os arquivos zip.
</p>
<p>
  A pasta deve ser criada dentro do diretório TSD no disco C:, especificamente na subpasta TMP (C:\\TSD\\TMP). <br/>
  <strong>Padrão de nomenclatura obrigatório para a pasta:</strong><br/>
  <code>XML (MÊS) (ANO) - (NOME DA EMPRESA)</code> <i>(Tudo em maiúsculo)</i>
</p>

<h2>3. Geração do Arquivo Zip com os XMLs</h2>
<p>Vá até o Host para gerar o arquivo. Siga os passos nas imagens abaixo:</p>

<h3>Passo 3.1: Menu NFC-e / NFe</h3>
<p>Na lateral esquerda, acesse a aba <strong>NFC-e / NFe</strong>.</p>
<img src="/static/images/xml_template/img1.png" style="max-width:100%; border-radius:8px; border: 1px solid #ddd; margin: 10px 0;" />

<h3>Passo 3.2: Acessar "Zip dos XML"</h3>
<p>Clique na opção <strong>Zip dos XML para envio de email</strong>.</p>
<img src="/static/images/xml_template/img2.png" style="max-width:100%; border-radius:8px; border: 1px solid #ddd; margin: 10px 0;" />

<h3>Passo 3.3: Preencher as opções</h3>
<p>
  Na janela de Compactação, preencha as datas e selecione a pasta criada:
  <ul>
    <li>Mês/Ano de referência e Data inicial/final.</li>
    <li>Marque a caixa <strong>Incluir XML cancelado</strong>.</li>
    <li>No diretório de destino, selecione a pasta criada no passo 2: <code>C:\\TSD\\TMP</code>.</li>
  </ul>
</p>
<p>
  <strong>IMPORTANTE:</strong> O arquivo zip deve ser gerado para três tipos diferentes de notas! Repita este mesmo processo de compactação clicando nas abas no topo da janela para:
  <ul>
    <li><strong>NFC-e</strong></li>
    <li><strong>NFe</strong></li>
    <li><strong>Notas Fornecedor</strong></li>
  </ul>
</p>
<img src="/static/images/xml_template/img3.png" style="max-width:100%; border-radius:8px; border: 1px solid #ddd; margin: 10px 0;" />
<img src="/static/images/xml_template/img6.png" style="max-width:100%; border-radius:8px; border: 1px solid #ddd; margin: 10px 0;" />

<h2>4. Geração do Mapa Resumo</h2>
<p>Após gerar os arquivos zip, você vai precisar gerar o mapa resumo com as NFC-e.</p>

<h3>Passo 4.1: Acessar "Mapa Resumo das NFC-e"</h3>
<p>Ainda na aba NFC-e, clique em <strong>Mapa Resumo das NFC-e</strong>.</p>
<img src="/static/images/xml_template/img4.png" style="max-width:100%; border-radius:8px; border: 1px solid #ddd; margin: 10px 0;" />

<h3>Passo 4.2: Preencher o Mapa Resumo</h3>
<p>Selecione a data vigente informada pelo cliente. Marque a opção de tipo como <strong>Detalhado</strong> e visualize.</p>
<img src="/static/images/xml_template/img5.png" style="max-width:100%; border-radius:8px; border: 1px solid #ddd; margin: 10px 0;" />

<h2>5. Compactação da Pasta e Envio por E-mail</h2>
<p>
  Após concluir a geração dos arquivos XML (NFC-e, NFe, Notas Fornecedor) e o Mapa Resumo, siga os passos finais:
</p>
<ul>
  <li>Vá na pasta original que foi criada com os arquivos do cliente (em <code>C:\\TSD\\TMP</code>) e <strong>faça a compactação</strong> (gere um arquivo .zip) de toda a pasta.</li>
  <li>Pegue o arquivo zip gerado e <strong>transfira (copie) para o seu próprio computador</strong> a partir do acesso remoto.</li>
  <li>Faça o envio do arquivo por e-mail, de acordo com o alinhamento feito com o cliente e com a contabilidade dele.</li>
</ul>
<p>
  <strong>Dica:</strong> Existe a possibilidade de pesquisar o e-mail da contabilidade na própria caixa de e-mail da empresa, pesquisando pelo nome da empresa do cliente!
</p>
"""

template.content_html = html_content
template.save()

print("Template 'Procedimento de Geração e Envio de XML' criado/atualizado com sucesso!")
