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
      if (campo.rotulo === "Completo" && dados.figurinhas) {
        valor.append(" ", botaoVer(dados, dados.figurinhas, "Figurinhas", "Ver figurinhas"));
      }
      if (campo.rotulo === "Conteúdo extra" && dados.extras) {
        valor.append(" ", botaoVer(dados, dados.extras, "Itens extras", "Ver extras"));
      }
      if (campo.rotulo === "Série fechada" && dados.serie) {
        const botao = document.createElement("button");
        botao.type = "button";
        botao.className = "botao-secundario";
        botao.textContent = "Ver números";
        botao.addEventListener("click", () => abrirSerie(dados));
        valor.append(" ", botao);
      }
      lista.append(termo, valor);
    }

    texto.append(titulo, codigo, lista);

    if (dados.editavel) {
      const editar = document.createElement("a");
      editar.className = "detalhe-editar";
      editar.href = `/${tipo}/${encodeURIComponent(dados.codigo)}/editar`;
      editar.textContent = "Editar campos";
      texto.append(editar);
    }

    if (dados.faixas && dados.faixas.length) {
      texto.append(montarFaixas(dados.faixas));
    }

    if (dados.capa_fonte) {
      const fonte = document.createElement("p");
      fonte.className = "detalhe-fonte";
      fonte.textContent = `Fonte da capa: ${dados.capa_fonte}`;
      texto.append(fonte);
    }

    corpo.append(figura, texto);
  }

  // Popup com os números de uma série fechada: capa de cada número e destaque nos que você tem.
  function abrirSerie(dados) {
    const serie = dados.serie;
    let caixa = document.getElementById("serie-popup");
    if (!caixa) {
      caixa = document.createElement("dialog");
      caixa.id = "serie-popup";
      caixa.className = "dialogo-figurinhas dialogo-serie";
      caixa.addEventListener("click", (e) => {
        if (e.target === caixa) caixa.close();
      });
      document.body.append(caixa);
    }
    caixa.replaceChildren();

    const titulo = document.createElement("h3");
    titulo.textContent = `Números de ${dados.titulo}`;

    const marcados = serie.itens.filter((item) => item.marcado).length;
    const resumo = document.createElement("p");
    resumo.textContent = `${marcados} de ${serie.total} marcados`;

    const grade = document.createElement("div");
    grade.className = "grade-serie";
    for (const item of serie.itens) {
      const cel = document.createElement("div");
      cel.className = "numero-serie" + (item.marcado ? " marcado" : "");
      const numero = document.createElement("span");
      numero.className = "numero-serie-n";
      numero.textContent = item.numero;
      cel.append(numero);
      if (item.capa) {
        const img = document.createElement("img");
        img.src = `/capas/${item.capa}`;
        img.alt = `Capa do número ${item.numero}`;
        img.loading = "lazy";
        cel.append(img);
      } else {
        const sem = document.createElement("div");
        sem.className = "numero-serie-sem";
        sem.textContent = "sem capa";
        cel.append(sem);
      }
      if (item.isbn10 || item.isbn13) {
        const isbns = document.createElement("div");
        isbns.className = "numero-serie-isbnx";
        if (item.isbn10) isbns.append(`ISBN-10: ${item.isbn10}`, document.createElement("br"));
        if (item.isbn13) isbns.append(`ISBN-13: ${item.isbn13}`);
        cel.append(isbns);
      }
      grade.append(cel);
    }

    const fechar = document.createElement("button");
    fechar.type = "button";
    fechar.className = "botao-secundario";
    fechar.textContent = "Fechar";
    fechar.addEventListener("click", () => caixa.close());

    caixa.append(titulo, resumo, grade, fechar);
    caixa.showModal();
  }

  function botaoVer(dados, parte, rotulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "botao-secundario";
    botao.textContent = texto;
    botao.addEventListener("click", () => abrirMarcados(dados, parte, rotulo));
    return botao;
  }

  // Segundo popup, por cima do detalhe: mostra cada número e destaca os marcados.
  function abrirMarcados(dados, parte, rotulo) {
    const { total, marcadas } = parte;
    const marcadasSet = new Set(marcadas);

    let caixa = document.getElementById("figurinhas-popup");
    if (!caixa) {
      caixa = document.createElement("dialog");
      caixa.id = "figurinhas-popup";
      caixa.className = "dialogo-figurinhas";
      caixa.addEventListener("click", (e) => {
        if (e.target === caixa) caixa.close();
      });
      document.body.append(caixa);
    }
    caixa.replaceChildren();

    const titulo = document.createElement("h3");
    titulo.textContent = `${rotulo} de ${dados.titulo}`;

    const resumo = document.createElement("p");
    resumo.textContent = total > 0
      ? `${marcadas.length} de ${total} marcados`
      : "Total não informado.";

    const grade = document.createElement("div");
    grade.className = "grade-figurinhas";
    for (let n = 1; n <= total; n++) {
      const numero = document.createElement("span");
      numero.className = "figurinha-mostra" + (marcadasSet.has(n) ? " marcada" : "");
      numero.textContent = n;
      grade.append(numero);
    }

    const fechar = document.createElement("button");
    fechar.type = "button";
    fechar.className = "botao-secundario";
    fechar.textContent = "Fechar";
    fechar.addEventListener("click", () => caixa.close());

    caixa.append(titulo, resumo, grade, fechar);
    caixa.showModal();
  }

  function montarFaixas(faixas) {
    const secao = document.createElement("section");
    secao.className = "detalhe-faixas";

    const cabeca = document.createElement("h3");
    cabeca.textContent = "Faixas";

    const lista = document.createElement("ol");
    for (const faixa of faixas) {
      const item = document.createElement("li");

      const numero = document.createElement("span");
      numero.className = "faixa-numero";
      numero.textContent = faixa.numero;

      const corpo = document.createElement("div");
      corpo.className = "faixa-corpo";
      const nome = document.createElement("span");
      nome.className = "faixa-titulo";
      nome.textContent = faixa.titulo;
      corpo.append(nome);
      if (faixa.autores) {
        const autores = document.createElement("span");
        autores.className = "faixa-autores";
        autores.textContent = faixa.autores;
        corpo.append(autores);
      }

      const duracao = document.createElement("span");
      duracao.className = "faixa-duracao";
      duracao.textContent = faixa.duracao || "";

      // Última coluna sempre existe, para o alinhamento não mudar sem clipe.
      const clipe = document.createElement("span");
      clipe.className = "faixa-clipe";
      if (faixa.youtube_url) {
        const link = document.createElement("a");
        link.href = faixa.youtube_url;
        link.target = "_blank";
        link.rel = "noopener";
        link.textContent = "Clipe";
        link.setAttribute("aria-label", `Clipe de ${faixa.titulo} no YouTube`);
        clipe.append(link);
      }

      item.append(numero, corpo, duracao, clipe);
      lista.append(item);
    }

    secao.append(cabeca, lista);
    return secao;
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

  // Seleção para as fichas (só aparece para quem está logado). Fica no navegador de quem seleciona,
  // então continua marcada ao trocar de página.
  const CHAVE_SELECAO = "fichas-selecao";
  const modoBox = document.getElementById("selecao-modo");
  const barra = document.getElementById("selecao-barra");
  const totalEl = document.getElementById("selecao-total");
  const gerar = document.getElementById("selecao-gerar");
  const limpar = document.getElementById("selecao-limpar");

  function lerSelecao() {
    try {
      return new Set(JSON.parse(localStorage.getItem(CHAVE_SELECAO) || "[]"));
    } catch (erro) {
      return new Set();
    }
  }

  function gravarSelecao(selecao) {
    try {
      localStorage.setItem(CHAVE_SELECAO, JSON.stringify([...selecao]));
    } catch (erro) {
      // Sem armazenamento disponível, a seleção vale só até a página mudar.
    }
  }

  function modoSelecao() {
    return Boolean(modoBox && modoBox.checked);
  }

  function chaveDo(cartao) {
    return `${cartao.dataset.tipo}:${cartao.dataset.codigo}`;
  }

  function atualizarSelecao() {
    const selecao = lerSelecao();
    document.body.classList.toggle("modo-selecao", modoSelecao());
    document.querySelectorAll(".cartao").forEach((cartao) => {
      const marcado = selecao.has(chaveDo(cartao));
      cartao.classList.toggle("selecionado", marcado);
      cartao.setAttribute("aria-pressed", marcado ? "true" : "false");
    });
    if (barra) barra.hidden = !modoSelecao();
    if (totalEl) totalEl.textContent = selecao.size;
    if (gerar) {
      gerar.href = "/fichas?" + [...selecao].map((c) => "i=" + encodeURIComponent(c)).join("&");
      gerar.style.pointerEvents = selecao.size ? "" : "none";
    }
  }

  function alternarSelecao(cartao) {
    const selecao = lerSelecao();
    const chave = chaveDo(cartao);
    if (selecao.has(chave)) {
      selecao.delete(chave);
    } else {
      selecao.add(chave);
    }
    gravarSelecao(selecao);
    atualizarSelecao();
  }

  if (modoBox) {
    modoBox.addEventListener("change", atualizarSelecao);
    if (limpar) {
      limpar.addEventListener("click", () => {
        gravarSelecao(new Set());
        atualizarSelecao();
      });
    }
    atualizarSelecao();
  }

  document.querySelectorAll(".cartao").forEach((cartao) => {
    cartao.addEventListener("click", () => {
      if (modoSelecao()) {
        alternarSelecao(cartao);
      } else {
        abrirDetalhe(cartao.dataset.tipo, cartao.dataset.codigo);
      }
    });
  });

  // Fecha ao clicar fora da caixa do popup.
  detalhe.addEventListener("click", (evento) => {
    if (evento.target === detalhe) detalhe.close();
  });
})();
