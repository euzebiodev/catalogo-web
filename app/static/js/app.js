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
