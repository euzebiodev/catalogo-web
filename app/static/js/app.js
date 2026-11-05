(() => {
  const detalhe = document.getElementById("detalhe");
  const corpo = document.getElementById("detalhe-corpo");
  if (!detalhe || !corpo) return;

  function montarDetalhe(tipo, dados) {
    corpo.replaceChildren();

    const figura = document.createElement("div");
    figura.className = `detalhe-capa formato-${tipo}`;
    if (dados.capa_arquivo) {
      const img = document.createElement("img");
      img.src = `/capas/${dados.capa_arquivo}`;
      img.alt = `Capa de ${dados.titulo}`;
      figura.append(img);
    } else {
      const vazio = document.createElement("div");
      vazio.className = "sem-capa";
      vazio.textContent = dados.titulo;
      figura.append(vazio);
    }

    const texto = document.createElement("div");
    texto.className = "detalhe-texto";

    const titulo = document.createElement("h2");
    titulo.id = "detalhe-titulo";
    titulo.textContent = dados.titulo;

    const codigo = document.createElement("p");
    codigo.className = "detalhe-codigo";
    codigo.textContent = dados.codigo;

    const lista = document.createElement("dl");
    for (const campo of dados.campos) {
      const termo = document.createElement("dt");
      termo.textContent = campo.rotulo;
      const valor = document.createElement("dd");
      valor.textContent = campo.valor;
      lista.append(termo, valor);
    }

    texto.append(titulo, codigo, lista);

    if (dados.capa_fonte) {
      const fonte = document.createElement("p");
      fonte.className = "detalhe-fonte";
      fonte.textContent = `Fonte da capa: ${dados.capa_fonte}`;
      texto.append(fonte);
    }

    corpo.append(figura, texto);
  }

  async function abrirDetalhe(tipo, codigo) {
    corpo.replaceChildren();
    detalhe.showModal();
    try {
      const resposta = await fetch(`/api/${tipo}/${encodeURIComponent(codigo)}`);
      if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
      montarDetalhe(tipo, await resposta.json());
    } catch (erro) {
      const aviso = document.createElement("p");
      aviso.className = "vazio";
      aviso.textContent = "Não foi possível carregar os dados deste item.";
      corpo.append(aviso);
      console.error(erro);
    }
  }

  document.querySelectorAll(".cartao").forEach((cartao) => {
    cartao.addEventListener("click", () => {
      abrirDetalhe(cartao.dataset.tipo, cartao.dataset.codigo);
    });
  });

  // Fecha ao clicar fora da caixa do popup.
  detalhe.addEventListener("click", (evento) => {
    if (evento.target === detalhe) detalhe.close();
  });
})();
