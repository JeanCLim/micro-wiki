# -*- coding: utf-8 -*-
import os
import re

def fix_models_py():
    models_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wiki', 'models.py')
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Expand allowed tags in Article.save for rich formatting
    old_tags = "allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a', 'h1', 'h2', 'h3', 'p', 'br', 'ul', 'ol', 'li', 'table', 'tbody', 'tr', 'td', 'img']"
    new_tags = "allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a', 'h1', 'h2', 'h3', 'p', 'br', 'ul', 'ol', 'li', 'table', 'tbody', 'tr', 'td', 'img', 'blockquote', 'code', 'pre', 'hr', 'div', 'span']"
    content = content.replace(old_tags, new_tags)

    old_attrs = "allowed_attributes = {'a': ['href', 'title'], 'img': ['src', 'alt', 'width', 'height']}"
    new_attrs = "allowed_attributes = {'a': ['href', 'title', 'target'], 'img': ['src', 'alt', 'width', 'height', 'style'], '*': ['class', 'style']}"
    content = content.replace(old_attrs, new_attrs)

    # We need to remove bogus clean() and save() from all classes except CustomUser
    lines = content.splitlines()
    new_lines = []
    current_class = None
    skip = False

    for line in lines:
        stripped = line.strip()
        if line.startswith('class '):
            current_class = line.split('class ')[1].split('(')[0].split(':')[0].strip()
            skip = False

        if current_class != 'CustomUser':
            if stripped == 'def clean(self):':
                skip = True
            elif stripped == 'def save(self, *args, **kwargs):' and 'self.full_clean()' in content:
                # Check if next line would be self.full_clean()
                skip = True
            elif stripped.startswith('def ') or stripped.startswith('class ') or (len(line) > 0 and not line.startswith(' ') and not line.startswith('\t')):
                skip = False
            elif skip and stripped == '':
                continue

        if not skip:
            new_lines.append(line)

    with open(models_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + '\n')
    print("models.py revisado com sucesso!")

fix_models_py()

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wiki.models import Company, Category, Article, CustomUser

def seed():
    # 1. Empresa TechCorp S.A.
    company, created = Company.objects.get_or_create(
        cnpj="12.345.678/0001-99",
        defaults={
            "name": "TechCorp S.A.",
            "domain": "techcorp.com.br",
            "is_active": True
        }
    )
    if not created:
        company.name = "TechCorp S.A."
        company.domain = "techcorp.com.br"
        company.is_active = True
        company.save()
    print(f"Empresa: {company.name} (CNPJ: {company.cnpj})")

    # 2. Categoria Suporte Técnico
    category, cat_created = Category.objects.get_or_create(
        slug="suporte-tecnico",
        company=company,
        defaults={
            "name": "Suporte Técnico",
            "description": "Base de conhecimento técnica para resolução de incidentes e suporte aos sistemas."
        }
    )
    if not cat_created:
        category.name = "Suporte Técnico"
        category.save()
    print(f"Categoria: {category.name} ({category.slug})")

    # 3. Autor
    author = CustomUser.objects.filter(is_superuser=True).first()
    if not author:
        author = CustomUser.objects.first()
    if not author:
        author = CustomUser.objects.create_superuser('techcorp_admin', 'admin@techcorp.com.br', 'Admin123!')

    # 4. Conteúdo do Artigo em HTML formatações ricas
    article_html = """
    <blockquote style="border-left: 4px solid #3b82f6; padding: 12px 16px; background-color: rgba(59, 130, 246, 0.1); margin: 16px 0; border-radius: 4px;">
        <strong>💡 Base de Conhecimento TechCorp S.A.</strong><br>
        <strong>Área:</strong> Suporte Técnico e Mensageria Fiscal (NFC-e / NF-e)<br>
        <strong>Sistema Operacional Afetado:</strong> Windows 7 (32 bits / x86) puro (sem atualizações automáticas)<br>
        <strong>Severidade:</strong> Alta
    </blockquote>

    <h2>Visão Geral do Incidente</h2>
    <p>Ao tentar realizar o envio, a consulta de status de serviço ou o cancelamento de uma <strong>NFC-e</strong> através do sistema <strong>TechCorp S.A.</strong>, a aplicação interrompe a comunicação e apresenta a seguinte rejeição:</p>
    
    <blockquote style="border-left: 4px solid #ef4444; padding: 12px 16px; background-color: rgba(239, 68, 68, 0.1); margin: 16px 0; border-radius: 4px;">
        <strong>🚨 Erro Retornado:</strong> "Erro Interno: 12175 - Erro HTTP: 0 - Um ou mais erros foram encontrados no certificado Secure Sockets Layer (SSL) enviado pelo servidor"
    </blockquote>

    <h3>Causa Raiz do Problema</h3>
    <p>O <strong>WebService da SEFAZ</strong> passou a exigir exclusivamente conexões criptografadas através do protocolo de segurança <strong>TLS 1.2</strong>. O sistema operacional <strong>Windows 7</strong> (compilação original x86 / 32 bits) não possui suporte nativo ativo a esse protocolo, resultando na falha imediata da negociação de segurança de transporte <strong>SSL/TLS</strong>.</p>
    <p>Em estações onde o <strong>Windows Update</strong> se encontra bloqueado ou inoperante, o pacote oficial da Microsoft que adiciona o suporte ao TLS 1.2 (<strong>KB3140245</strong>) falha ao ser executado diretamente, exibindo a mensagem: <em>“A atualização não pode ser aplicada ao seu computador”</em>. Isso ocorre porque o sistema operacional carece do pacote de pré-requisitos fundamental: o <strong>Service Pack 1 (SP1)</strong>.</p>

    <hr style="margin: 24px 0; border: 0; border-top: 1px solid var(--border-color, #e2e8f0);">

    <h2>Configuração Inicial (Opções da Internet)</h2>
    <p>Antes de realizar a instalação das atualizações manuais no sistema operacional, é obrigatório ajustar as flags dos protocolos de segurança e de verificação de certificados no painel do Windows:</p>

    <ol style="margin-left: 20px; line-height: 1.8;">
        <li>Abra o <strong>Painel de Controle</strong> do Windows e acesse <strong>Opções da Internet</strong> (ou digite <code>inetcpl.cpl</code> no menu Executar).</li>
        <li>Selecione a aba <strong>Avançadas</strong>.</li>
        <li>Na caixa de listagem <strong>Configurações</strong>, role até a seção final de segurança e aplique os seguintes ajustes:
            <ul>
                <li><strong>Marque</strong> a opção <strong>Usar TLS 1.2</strong>.</li>
                <li><strong>Desmarque</strong> as opções <strong>Usar TLS 1.0</strong> e <strong>Usar TLS 1.1</strong> (opcional, para forçar o uso estrito do protocolo compatível).</li>
                <li><strong>Desmarque</strong> a opção <strong>Verificar revogação de certificados do servidor*</strong> (isso evita timeouts na consulta de revogação da cadeia SSL da SEFAZ).</li>
                <li><strong>Desmarque</strong> a opção <strong>Verificar se há certificados revogados do editor</strong>.</li>
            </ul>
        </li>
        <li>Clique no botão <strong>Aplicar</strong> e depois em <strong>OK</strong> para salvar.</li>
    </ol>

    <hr style="margin: 24px 0; border: 0; border-top: 1px solid var(--border-color, #e2e8f0);">

    <h2>Procedimento de Solução Definitiva (Atualização Manual do SO)</h2>
    <p>Para estações com Windows 7 (32 bits / x86) puro sem acesso ao Windows Update, a resolução exige o download e a execução manual dos pacotes da Microsoft respeitando <strong>rigorosamente a ordem cronológica</strong> abaixo.</p>

    <h3>Fase 1 - Pré-requisito (Instalação do SP1)</h3>
    <p>O <strong>Service Pack 1 (SP1)</strong> é o pacote base de infraestrutura do Windows 7. Sem ele, o sistema operacional não aceita a instalação de pacotes criptográficos mais recentes.</p>
    
    <ol style="margin-left: 20px; line-height: 1.8;">
        <li>Acesse o <strong>Catálogo do Microsoft Update</strong> através do navegador web.</li>
        <li>Pesquise pelo código <strong>KB976932</strong> na barra de busca do catálogo.</li>
        <li>Localize e faça o download do instalador autônomo específico para a arquitetura <strong>Windows 7 x86 (32 bits)</strong>.</li>
        <li>Execute o arquivo baixado e siga o assistente de instalação do Service Pack 1.</li>
        <li><strong>Reinicie obrigatoriamente a estação de trabalho</strong> após o término da instalação para que o kernel do Windows aplique os novos arquivos de sistema.</li>
    </ol>

    <blockquote style="border-left: 4px solid #f59e0b; padding: 12px 16px; background-color: rgba(245, 158, 11, 0.1); margin: 16px 0; border-radius: 4px;">
        <strong>⚠️ Atenção Analista:</strong> Nunca pule a <strong>Fase 1</strong>. Tentar executar o instalador da <strong>Fase 2</strong> (TLS 1.2) em um Windows 7 sem o pacote <strong>KB976932</strong> (SP1) resultará no erro de incompatibilidade <em>"A atualização não pode ser aplicada ao seu computador"</em>.
    </blockquote>

    <h3>Fase 2 - Habilitação do TLS 1.2</h3>
    <p>Com o <strong>Service Pack 1</strong> consolidado no sistema operacional, o Windows 7 está apto a receber as bibliotecas de criptografia modernas.</p>
    
    <ol style="margin-left: 20px; line-height: 1.8;">
        <li>Acesse novamente o <strong>Catálogo do Microsoft Update</strong>.</li>
        <li>Pesquise pelo código de atualização <strong>KB3140245</strong>.</li>
        <li>Faça o download da compilação específica para <strong>Windows 7 32 bits (x86)</strong>.</li>
        <li>Execute o arquivo <code>.msu</code> baixado e autorize a instalação do patch de segurança.</li>
        <li>Aguarde até que o instalador do Windows confirme que o pacote <strong>KB3140245</strong> foi instalado com êxito.</li>
    </ol>

    <h3>Fase 3 - Validação</h3>
    <p>Para assegurar que o sistema operacional incorporou as novas chaves TLS 1.2 e que o PDV da <strong>TechCorp S.A.</strong> restabeleceu a comunicação fiscal:</p>
    
    <ol style="margin-left: 20px; line-height: 1.8;">
        <li>Efetue uma <strong>última reinicialização</strong> do computador para aplicar as chaves de registro do protocolo <strong>TLS 1.2</strong>.</li>
        <li>Abra o sistema de automação da <strong>TechCorp S.A.</strong> e acesse o módulo fiscal de NFC-e.</li>
        <li>Realize os seguintes testes de homologação/produção:
            <ul>
                <li><strong>Consulta de Status de Serviço:</strong> Execute a consulta de status da SEFAZ para comprovar que o retorno HTTP é bem-sucedido (<em>"Serviço em Operação"</em>).</li>
                <li><strong>Emissão de NFC-e:</strong> Transmita uma nota fiscal de venda para validar a assinatura e a autorização instantânea da SEFAZ pelo protocolo TLS 1.2 sem ocorrência do <strong>Erro 12175</strong>.</li>
            </ul>
        </li>
    </ol>

    <blockquote style="border-left: 4px solid #10b981; padding: 12px 16px; background-color: rgba(16, 185, 129, 0.1); margin: 16px 0; border-radius: 4px;">
        <strong>✅ Homologação Concluída:</strong> Comunicação fiscal restabelecida com sucesso com a SEFAZ através de criptografia TLS 1.2.
    </blockquote>
    """

    article, art_created = Article.objects.get_or_create(
        slug="erro-12175-tls-12-windows-7",
        defaults={
            "title": "[Troubleshooting] Erro 12175 - Rejeição de TLS 1.2 no Windows 7",
            "content": article_html,
            "category": category,
            "author": author,
            "status": "APPROVED",
            "visibility": "PUBLIC",
            "version": "1.0",
            "responsible_area": "Suporte Técnico N3 - Mensageria Fiscal",
            "changes_summary": "Artigo inicial de troubleshooting para Erro 12175 no Windows 7."
        }
    )
    if not art_created:
        article.title = "[Troubleshooting] Erro 12175 - Rejeição de TLS 1.2 no Windows 7"
        article.content = article_html
        article.category = category
        article.status = "APPROVED"
        article.visibility = "PUBLIC"
        article.author = author
        article.save()

    print(f"Artigo criado/atualizado: {article.title} (Slug: {article.slug}) - Categoria: {article.category.name}")

if __name__ == '__main__':
    seed()
