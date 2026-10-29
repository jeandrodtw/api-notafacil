import shutil
import tempfile
from datetime import date, timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from . import garantia
from .models import Nota

# As fotos dos testes vão para uma pasta temporária (não suja a pasta media/)
MEDIA_TESTE = tempfile.mkdtemp()


def criar_imagem(nome="nota.jpg"):
    """Gera uma imagem JPEG pequena em memória para o upload."""
    buffer = BytesIO()
    Image.new("RGB", (10, 10), "blue").save(buffer, format="JPEG")
    return SimpleUploadedFile(nome, buffer.getvalue(), content_type="image/jpeg")


class AuthTests(APITestCase):
    def test_registro_sucesso(self):
        resp = self.client.post("/api/auth/registro/", {"username": "maria", "password": "123456"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", resp.data)
        self.assertTrue(User.objects.filter(username="maria").exists())

    def test_registro_usuario_duplicado(self):
        User.objects.create_user("maria", password="123456")
        resp = self.client.post("/api/auth/registro/", {"username": "maria", "password": "123456"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["username"][0], "Este usuário já existe.")

    def test_registro_usuario_curto(self):
        resp = self.client.post("/api/auth/registro/", {"username": "ab", "password": "123456"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["username"][0], "O usuário deve ter ao menos 3 caracteres.")

    def test_registro_senha_curta(self):
        resp = self.client.post("/api/auth/registro/", {"username": "maria", "password": "123"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["password"][0], "A senha deve ter ao menos 6 caracteres.")

    def test_login_valido_reutiliza_token(self):
        usuario = User.objects.create_user("maria", password="123456")
        token = Token.objects.create(user=usuario)
        resp = self.client.post("/api/auth/login/", {"username": "maria", "password": "123456"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {"token": token.key})

    def test_login_invalido(self):
        User.objects.create_user("maria", password="123456")
        resp = self.client.post("/api/auth/login/", {"username": "maria", "password": "errada"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data, {"detail": "Usuário ou senha inválidos."})

    def test_eu_com_token_valido(self):
        usuario = User.objects.create_user("maria", password="123456")
        token = Token.objects.create(user=usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        resp = self.client.get("/api/auth/eu/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {"id": usuario.id, "username": "maria"})

    def test_notas_sem_token_retorna_401(self):
        resp = self.client.get("/api/notas/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", resp.data)

    def test_notas_com_token_invalido_retorna_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token tokenquenaoexiste")
        resp = self.client.get("/api/notas/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(MEDIA_ROOT=MEDIA_TESTE)
class NotaTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TESTE, ignore_errors=True)

    def setUp(self):
        self.usuario = User.objects.create_user("maria", password="123456")
        token = Token.objects.create(user=self.usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def criar_nota(self, usuario=None, **campos):
        dados = {
            "usuario": usuario or self.usuario,
            "descricao_produto": "Smart TV",
            "data_compra": timezone.localdate(),
            "tempo_garantia_meses": 12,
            "loja": "Magazine Luiza",
        }
        dados.update(campos)
        return Nota.objects.create(**dados)

    # --- CRUD ---

    def test_criar_nota_json(self):
        resp = self.client.post(
            "/api/notas/",
            {
                "descricaoProduto": "Geladeira",
                "dataCompra": "10/03/2025",
                "tempoGarantiaMeses": 12,
                "loja": "Casas Bahia",
                "assistenciaTecnica": "Brastemp Serviços",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["descricaoProduto"], "Geladeira")
        self.assertIsNone(resp.data["fotoUri"])
        self.assertEqual(Nota.objects.get().usuario, self.usuario)

    def test_criar_nota_sem_campos_obrigatorios(self):
        resp = self.client.post("/api/notas/", {"dataCompra": "10/03/2025"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("descricaoProduto", resp.data)
        self.assertIn("loja", resp.data)
        self.assertEqual(resp.data["loja"][0], "Este campo é obrigatório.")

    def test_garantia_negativa(self):
        resp = self.client.post(
            "/api/notas/",
            {"descricaoProduto": "TV", "dataCompra": "10/03/2025", "tempoGarantiaMeses": -1, "loja": "X"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tempoGarantiaMeses", resp.data)

    def test_listar_notas(self):
        self.criar_nota(descricao_produto="TV")
        self.criar_nota(descricao_produto="Notebook")
        resp = self.client.get("/api/notas/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Mais recentes primeiro
        self.assertEqual([n["descricaoProduto"] for n in resp.data], ["Notebook", "TV"])

    def test_buscar_por_descricao_ou_loja(self):
        self.criar_nota(descricao_produto="TV", loja="Magazine Luiza")
        self.criar_nota(descricao_produto="Notebook", loja="Kabum")
        resp = self.client.get("/api/notas/?busca=kabum")
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["descricaoProduto"], "Notebook")

    def test_detalhe_nota(self):
        nota = self.criar_nota()
        resp = self.client.get(f"/api/notas/{nota.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], nota.id)

    def test_editar_nota_patch(self):
        nota = self.criar_nota()
        resp = self.client.patch(f"/api/notas/{nota.id}/", {"loja": "Fast Shop"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        nota.refresh_from_db()
        self.assertEqual(nota.loja, "Fast Shop")

    def test_editar_nota_put(self):
        nota = self.criar_nota()
        dados = {
            "descricaoProduto": "TV 65",
            "dataCompra": "01/02/2025",
            "tempoGarantiaMeses": 24,
            "loja": "Carrefour",
            "assistenciaTecnica": "",
        }
        resp = self.client.put(f"/api/notas/{nota.id}/", dados, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["descricaoProduto"], "TV 65")
        self.assertEqual(resp.data["tempoGarantiaMeses"], 24)

    def test_apagar_nota(self):
        nota = self.criar_nota()
        resp = self.client.delete(f"/api/notas/{nota.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Nota.objects.exists())

    # --- Isolamento entre usuários ---

    def test_usuario_nao_ve_nota_de_outro(self):
        outro = User.objects.create_user("joao", password="123456")
        nota_do_outro = self.criar_nota(usuario=outro)

        self.assertEqual(self.client.get("/api/notas/").data, [])
        resp = self.client.get(f"/api/notas/{nota_do_outro.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_usuario_nao_edita_nem_apaga_nota_de_outro(self):
        outro = User.objects.create_user("joao", password="123456")
        nota_do_outro = self.criar_nota(usuario=outro, loja="Original")

        resp = self.client.patch(f"/api/notas/{nota_do_outro.id}/", {"loja": "Hackeada"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        resp = self.client.delete(f"/api/notas/{nota_do_outro.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        nota_do_outro.refresh_from_db()
        self.assertEqual(nota_do_outro.loja, "Original")

    # --- Datas e garantia ---

    def test_data_formato_brasileiro(self):
        resp = self.client.post(
            "/api/notas/",
            {"descricaoProduto": "TV", "dataCompra": "31/01/2025", "tempoGarantiaMeses": 1, "loja": "X"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["dataCompra"], "31/01/2025")
        self.assertEqual(resp.data["dataVencimento"], "28/02/2025")  # fevereiro não tem dia 31
        self.assertEqual(Nota.objects.get().data_compra, date(2025, 1, 31))

    def test_data_formato_iso_tambem_aceito(self):
        resp = self.client.post(
            "/api/notas/",
            {"descricaoProduto": "TV", "dataCompra": "2025-03-10", "loja": "X"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["dataCompra"], "10/03/2025")

    def test_data_invalida(self):
        resp = self.client.post(
            "/api/notas/",
            {"descricaoProduto": "TV", "dataCompra": "31/13/2025", "loja": "X"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dataCompra", resp.data)

    def test_funcao_status_garantia(self):
        hoje = date(2025, 6, 15)
        compra = date(2025, 1, 15)
        self.assertEqual(garantia.status_garantia(compra, 12, hoje), "vigente")  # vence 15/01/2026
        self.assertEqual(garantia.status_garantia(compra, 6, hoje), "vencendo")  # vence 15/07 (30 dias)
        self.assertEqual(garantia.status_garantia(compra, 5, hoje), "vencendo")  # vence hoje
        self.assertEqual(garantia.status_garantia(compra, 4, hoje), "vencida")  # venceu 15/05/2025
        self.assertEqual(garantia.status_garantia(date(2025, 1, 16), 6, hoje), "vigente")  # 31 dias

    def test_status_garantia_na_api_e_filtro(self):
        hoje = timezone.localdate()
        self.criar_nota(descricao_produto="Vigente", data_compra=hoje, tempo_garantia_meses=12)
        self.criar_nota(descricao_produto="Vencendo", data_compra=hoje - timedelta(days=10), tempo_garantia_meses=1)
        self.criar_nota(descricao_produto="Vencida", data_compra=hoje - timedelta(days=400), tempo_garantia_meses=12)

        resp = self.client.get("/api/notas/")
        status_por_nota = {n["descricaoProduto"]: n["statusGarantia"] for n in resp.data}
        self.assertEqual(status_por_nota, {"Vigente": "vigente", "Vencendo": "vencendo", "Vencida": "vencida"})

        resp = self.client.get("/api/notas/?status=vencendo")
        self.assertEqual([n["descricaoProduto"] for n in resp.data], ["Vencendo"])

        resp = self.client.get("/api/notas/?status=qualquer")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", resp.data)

    # --- Foto ---

    def test_criar_nota_com_foto(self):
        resp = self.client.post(
            "/api/notas/",
            {
                "descricaoProduto": "Celular",
                "dataCompra": "10/03/2025",
                "tempoGarantiaMeses": 12,
                "loja": "Fast Shop",
                "fotoUri": criar_imagem(),
            },
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # A URL volta absoluta, pronta para o <Image source={{ uri }} /> do app
        self.assertTrue(resp.data["fotoUri"].startswith("http://testserver/media/notas/"))
        self.assertTrue(Nota.objects.get().foto)

    def test_trocar_foto_apaga_a_antiga(self):
        nota = self.criar_nota(foto=criar_imagem("antiga.jpg"))
        caminho_antigo = nota.foto.path

        resp = self.client.patch(f"/api/notas/{nota.id}/", {"fotoUri": criar_imagem("nova.jpg")}, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("nova", resp.data["fotoUri"])
        self.assertFalse(Nota.objects.get().foto.storage.exists(caminho_antigo))

    def test_reenviar_url_da_foto_mantem_a_foto(self):
        nota = self.criar_nota(foto=criar_imagem())
        url = self.client.get(f"/api/notas/{nota.id}/").data["fotoUri"]
        resp = self.client.patch(f"/api/notas/{nota.id}/", {"fotoUri": url, "loja": "Nova"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["fotoUri"], url)

    def test_apagar_nota_apaga_a_foto(self):
        nota = self.criar_nota(foto=criar_imagem())
        caminho = nota.foto.path
        self.client.delete(f"/api/notas/{nota.id}/")
        self.assertFalse(nota.foto.storage.exists(caminho))

    def test_arquivo_que_nao_e_imagem(self):
        arquivo = SimpleUploadedFile("nota.txt", b"nao sou imagem", content_type="text/plain")
        resp = self.client.post(
            "/api/notas/",
            {"descricaoProduto": "TV", "dataCompra": "10/03/2025", "loja": "X", "fotoUri": arquivo},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fotoUri", resp.data)

    def test_imagem_maior_que_5mb(self):
        # BMP sem compressão: 1400 x 1400 x 3 bytes ≈ 5,9 MB
        buffer = BytesIO()
        Image.new("RGB", (1400, 1400), "red").save(buffer, format="BMP")
        imagem = SimpleUploadedFile("grande.bmp", buffer.getvalue(), content_type="image/bmp")
        resp = self.client.post(
            "/api/notas/",
            {"descricaoProduto": "TV", "dataCompra": "10/03/2025", "loja": "X", "fotoUri": imagem},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["fotoUri"][0], "A imagem deve ter no máximo 5 MB.")
