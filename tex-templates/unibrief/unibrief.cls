% Document Class 'unibrief'
%  by K.Braune, RZ Uni Karlsruhe
%
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{unibrief}
%
% Basisklasse 'dinbrief' laden:
\LoadClass[a4paper]{dinbrief}
%
% Generell benoetigte Pakete laden:
\RequirePackage{helvet}
\RequirePackage{german}
\RequirePackage{graphicx}
%
\renewcommand{\rmdefault}{phv}
\setlength\textwidth{17cm}
\addtolength{\textheight}{-3mm}
%
\enabledraftstandard
\nowindowrules
\windowtics
\pagestyle{plain}
%
% Abaendern von dinbrief-Befehlen:
\let\@uka@Conc=\subject
\renewcommand{\subject}[1]{\@uka@Conc{\bfseries\@uka@vsp\\#1}}
\let\concern=\subject
%
\gdef\@uka@az{\relax}
\gdef\@uka@ym{\relax}
%
\let\Betreff=\subject
\newcommand{\AZ}[1]{\gdef\@uka@az{#1}}
\let\sign=\AZ
\newcommand{\IZ}[1]{\gdef\@uka@ym{#1}}
\let\yourmail=\IZ
\gdef\ka@db@tswindowtics{%
  \vbox to 0pt{%
    \rule{0pt}{83truemm}% 62.5truemm > 80.0truemm
    \hbox to 0pt{\hspace*{-16.3truemm}$\scriptstyle\bullet$\hss}%
    \vss}\nointerlineskip
  }
\let\@uka@date=\@date
\gdef\@date{\phantom{\@uka@date}}
\gdef\date#1{\gdef\@uka@date{#1}\gdef\@ntoday{#1}}
\let\Datum=\date
%
\gdef\writer#1{\relax}
\gdef\backaddress#1{\relax}
\def\phone#1#2{\relax}
%
% Seitenstil:
\def\ps@uka{% Wie <plain>, aber Folgeseiten unten numeriert
  \headheight=\lts@headheight
  \headsep=\lts@headsep
  \ifka@db@ltxtwoe
      \relax
    \else
      \footheight 4.2truemm
    \fi
  \footskip 8.8truemm
  \def\@oddhead{}
  \def\@oddfoot{\hfil{\fontsize{8}{12pt}\selectfont\mdseries-~\thepage~-}\hfil}
  \def\@evenhead{}
  \def\@evenfoot{}
  }
%
\newlength{\@uka@Wd}
\newlength{\@uka@Spc}
\setlength{\@uka@Spc}{4.5cm}
\newlength{\@uka@vsk}
\newif{\if@uka@}
\newif{\if@uka@LA@}
%
\@uka@LA@false
\gdef\@uka@Uka{Universit"at Karlsruhe (TH)}
\gdef\@uka@ULogo{unilogo.pdf}
\gdef\@uka@Inst{\relax}                 % zwingend!
\gdef\@uka@ILogo{\relax}
\gdef\@uka@Abt{\relax}
\gdef\@uka@Ber{\relax}
\gdef\@uka@Str{Kaiserstr.~12}
\gdef\@uka@Geb{\relax}
\gdef\@uka@Ort{76131 Karlsruhe}
\gdef\@uka@FOrt{76128 Karlsruhe}
\gdef\@uka@FInst{\relax}
\gdef\@uka@FInstZ{\relax}
\gdef\@uka@TelZ{6 08-0}
\gdef\@uka@TelVZ{(0721)}
\gdef\@uka@TelE{6 08}
\gdef\@uka@FaxE{6 08}
\gdef\@uka@FaxVE{(0721)}
\gdef\@uka@WWW{www.uni-karlsruhe.de}
%
% Persoenliche Angaben:
\gdef\@uka@Func{\relax}
\gdef\@uka@Tit{\relax}
\gdef\@uka@Name{\relax}                 % zwingend!
\gdef\@uka@Tel{\relax}                  % zwingend!
\gdef\@uka@Fax{\relax}
\gdef\@uka@Email{\relax}                % zwingend!
%
% Institutsspezifische Angaben:
\newcommand{\Inst}[1]{\gdef\@uka@Inst{{#1}}}
\newcommand{\FInst}[1]{\gdef\@uka@FInst{{#1}}}
\newcommand{\FInstZeile}[1]{\gdef\@uka@FInstZ{{#1}}}
\newcommand{\Logo}[1]{\gdef\@uka@ILogo{{#1}}}
\newcommand{\Abteilung}[1]{\gdef\@uka@Abt{{#1}}}
\newcommand{\Bereich}[1]{\gdef\@uka@Ber{{#1}}}
\newcommand{\Strasse}[1]{\gdef\@uka@Str{{#1}}}
\newcommand{\Geb}[1]{\gdef\@uka@Geb{{#1}}}
\newcommand{\Ort}[1]{\gdef\@uka@Ort{{#1}}}
\let\place=\Ort
\newcommand{\FOrt}[1]{\gdef\@uka@FOrt{{#1}}}
\newcommand{\TelZentral}[1]{\gdef\@uka@TelZ{{#1}}}
\newcommand{\TelVorwahl}[1]{\gdef\@uka@TelVZ{{(0721)}}}
\newcommand{\TelInst}[1]{\gdef\@uka@TelE{{#1}}}
\newcommand{\FaxInst}[1]{\gdef\@uka@FaxE{{#1}}}
\newcommand{\FaxVorwahl}[1]{\gdef\@uka@FaxVE{{(0721)}}}
\newcommand{\EmailDomain}[1]{\gdef\@uka@EmailE{{#1}}}
\newcommand{\WWW}[1]{\gdef\@uka@WWW{{#1}}}
\newcommand{\Lieferanschrift}{\@uka@LA@true}
%
% Persoenliche Angaben:
\newcommand{\Funktion}[1]{\gdef\@uka@Func{{#1}}}
\newcommand{\Titel}[1]{\gdef\@uka@Tit{{#1}}}
\newcommand{\Name}[1]{\gdef\@uka@Name{{#1}}}
% Telefonnummer: \@uka@TelE-\@uka@Tel
\newcommand{\Tel}[1]{\gdef\@uka@Tel{{#1}}}
% Faxnummer: \@uka@FaxE-\@uka@Fax
\newcommand{\Fax}[1]{\gdef\@uka@Fax{{#1}}}
% E-Mail: \@uka@Email\\\@uka@EmailE
\newcommand{\Email}[1]{\gdef\@uka@Email{{#1}}}
%
%
% Setzen des Briefkopfes:
%
\newsavebox{\@uka@box}
%
\newcommand{\@uka@Kopf}{%
  \savebox{\@uka@box}[4.8cm][l]{\parbox[t]{4.8cm}{\raggedright%
    \fontsize{8}{12pt}\selectfont%
    \@uka@false%
    \if\@uka@Ber\relax\relax\else{\fontseries{b}\selectfont\@uka@Ber}\\\@uka@true\fi
    \if\@uka@Func\relax\relax\else{\@uka@Func}\\\@uka@true\fi
    \if\@uka@Tit\relax\relax\else{\@uka@Tit}\\\@uka@true\fi
    \if\@uka@Name\relax\relax\else{\@uka@Name}\\\@uka@true\fi
    \if@uka@\vspace{6pt}\@uka@false\fi
    \if@uka@LA@{Lieferanschrift:}\\\fi
    \@uka@Str\if\@uka@Geb\relax\relax\else, Geb.~\@uka@Geb\fi\\
    \@uka@Ort\\
    \settowidth{\@uka@Wd}{Fax: \@uka@FaxVE}%
    \makebox[\@uka@Wd]{Tel.: \hfill\@uka@TelVZ} \@uka@TelZ\\
    \makebox[\@uka@Wd][l]{Durchwahl:} \@uka@TelE%
      \if\@uka@Tel\relax\relax\else-\@uka@Tel\fi\\
    \makebox[\@uka@Wd]{Fax: \hfill\@uka@FaxVE} \@uka@FaxE%
      \if\@uka@Fax\relax\relax\else-\@uka@Fax\fi\\[6pt]
    E-Mail: \@uka@Email\\
    \@uka@EmailE\\%[6pt]
    \@uka@WWW%\\[6pt]
    \if\@uka@az\relax\relax\else\\[6pt]%
      AZ:\quad \@uka@az\fi%
    \if\@uka@ym\relax\relax\else\\[6pt]%
      \yourmailmsg:\\\@uka@ym\fi%
    \\[6pt]%
    \@uka@date%
    }\hss}%
  \settodepth{\@uka@Wd}{\usebox{\@uka@box}}%
  \addtolength{\@uka@Wd}{-\@uka@Spc}% Sollte >= 0 sein!
  \ifdim\@uka@Wd<0pt%
    \global\@uka@vsk=0pt%
   \else%
    \global\@uka@vsk=\@uka@Wd%
   \fi%
  \gdef\@uka@vsp{\rule{0pt}{\@uka@vsk}}%
  %
  \vspace{6.2mm}%
  \raisebox{.5pt}{\includegraphics[height=33.5pt]{\@uka@ULogo}}\hspace{2.4mm}
  \parbox[b]{.85\textwidth}{\fontseries{m}\fontsize{14}{16.1pt}\selectfont%
    \@uka@Uka\\[2pt]%
    \fontsize{14}{12pt}\fontseries{b}\selectfont\@uka@Inst}
  \vbox to 0pt{\vss\hspace*{31.5bp}\hspace*{5mm}%
    \fontsize{8}{12pt}\fontseries{b}\selectfont%
    \if\@uka@Abt\relax\relax\else\@uka@Abt\fi%
    }%
  \vspace{19.385mm}

  {\fontsize{8}{12pt}\selectfont%
  \parbox[t]{90mm}{\@uka@Uka~$\cdot$~%
    \if\@uka@FInst\relax\relax\else\@uka@FInst~$\cdot$~\fi%
    \if\@uka@FOrt\relax\@uka@Ort\else\@uka@FOrt\fi\hfill%
    \if\@uka@FInstZ\relax\relax\else\\\@uka@FInstZ\hfill\fi}%
  \hfill%
  \usebox{\@uka@box}%
\iffalse
  \parbox[t]{4cm}{\parbox[t]{4.8cm}{\raggedright%
    \@uka@false%
    \if\@uka@Ber\relax\relax\else{\fontseries{b}\selectfont\@uka@Ber}\\\@uka@true\fi
    \if\@uka@Func\relax\relax\else{\@uka@Func}\\\@uka@true\fi
    \if\@uka@Tit\relax\relax\else{\@uka@Tit}\\\@uka@true\fi
    \if\@uka@Name\relax\relax\else{\@uka@Name}\\\@uka@true\fi
    \if@uka@\vspace{6pt}\@uka@false\fi
    \if@uka@LA@{Lieferanschrift:}\\\fi
    \@uka@Str\if\@uka@Geb\relax\relax\else, Geb.~\@uka@Geb\fi\\
    \@uka@Ort\\
    \settowidth{\@uka@Wd}{Fax: \@uka@FaxVE}%
    \makebox[\@uka@Wd]{Tel.: \hfill\@uka@TelVZ} \@uka@TelZ\\
    \makebox[\@uka@Wd][l]{Durchwahl:} \@uka@TelE%
      \if\@uka@Tel\relax\relax\else-\@uka@Tel\fi\\
    \makebox[\@uka@Wd]{Fax: \hfill\@uka@FaxVE} \@uka@FaxE%
      \if\@uka@Fax\relax\relax\else-\@uka@Fax\fi\\[6pt]
    E-Mail: \@uka@Email\\
    \@uka@EmailE\\[6pt]
    \@uka@WWW%\\[6pt]
    \if\@uka@az\relax\relax\else\\[6pt]%
      %\makebox[\@uka@Wd][l]{AZ:} \@uka@az\fi%
      AZ: \@uka@az\fi%
    \if\@uka@ym\relax\relax\else\\[6pt]%
      \yourmailmsg:\\\@uka@ym\fi%
    \\[6pt]%
    \@uka@date%
    }\hss}%
\fi
  }
}
%
\EmailDomain{@uni-karlsruhe.de}
%
% Einlesen der Angaben zur Institution und zur Person (angegeben als Optionen):
%
\DeclareOption*{\InputIfFileExists{\CurrentOption.tex}{}{}}
\ProcessOptions
%
% Pruefen, ob alle erforderlichen Angaben vorhanden sind:
\if\@uka@Inst\relax%
  \InputIfFileExists{inst.tex}{}{}
  \if\@uka@Inst\relax\message{Es muss mit dem Befehl \string\Inst\{...\} eine Institution angegeben werden.}\fi
\fi
%
\address{\@uka@Kopf}
\pagestyle{uka}
\subject{\phantom{.}}
%
\if\@uka@ILogo\relax\relax\else%
  \let\@uka@open=\opening
  \gdef\opening{\bottomtext{\mbox{}\hfill\parbox[b]{4cm}{\@uka@ILogo}}\@uka@open}
 \fi
