package knowledge.modeling;

import knowledge.testing.DistanceBranchParser;
import org.w3c.dom.Element;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.stream.Collectors;

public class CodeGenerator {
    Finder finder;
    ArrayList<CodePiece> codePieces = new ArrayList<>();
    boolean forTesting = false;

    public void setFinder(Finder finder) {
        this.finder = finder;
    }

    public void setForTesting(boolean forTesting) {
        this.forTesting = forTesting;
    }

    public void generate() {
        finder.getRoots().stream().forEach(r -> {
            generate(r);
        });
    }

    void generate(Element root) {
        finder.forEach(root, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Class"),
                e -> {
                    CodePiece codePiece = new CodePiece();
                    generateClassCode(e, codePiece);
                    codePieces.add(codePiece);
                    codePiece.setName(getPackage(e) + "." + e.getAttribute("name"));
                });
        finder.forEach(root, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Interface"),
                e -> {
                    CodePiece codePiece = new CodePiece();
                    generateInterfaceCode(e, codePiece);
                    codePieces.add(codePiece);
                    codePiece.setName(getPackage(e) + "." + e.getAttribute("name"));
                });
        finder.forEach(root, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:DataType"),
                e -> {
                    CodePiece codePiece = new CodePiece();
                    generateDataTypeCode(e, codePiece);
                    codePieces.add(codePiece);
                    codePiece.setName(getPackage(e) + "." + e.getAttribute("name"));
                });
        finder.forEach(root, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Signal"),
                e -> {
                    CodePiece codePiece = new CodePiece();
                    generateSignalCode(e, codePiece);
                    codePieces.add(codePiece);
                    codePiece.setName(getPackage(e) + "." + e.getAttribute("name"));
                });
    }

    void generateClassCode(Element element, CodePiece codePiece) {
        boolean[] hasPrev = { false };
        String elementPackage = getPackage(element);
        codePiece.append("package " + elementPackage + ";\n\n");
        codePiece.append("public class " + element.getAttribute("name") +
                generateGeneralizationIfExists(element, null,
                        new ArrayList<>(Arrays.asList(new String[] { "xstate.core.InputReceiver" }))) + " {\n");
        codePiece.block(() -> {
            codePiece.append("final static String classifierId = \"" + getPackage(element) + "." + element.getAttribute("name") + "\";\n");
            codePiece.append("java.util.ArrayList<xstate.modeling.State> stateMachines = new java.util.ArrayList<>();\n\n");
            finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Property"), e -> {
                generatePropertyCode(e, codePiece);
            });
            // constructor
            codePiece.append("\n");
            codePiece.append("public " + element.getAttribute("name") + "() {\n");
            codePiece.block(() -> {
                codePiece.append("initializeBehavior();\n");
            });
            codePiece.append("}\n");
            finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Operation"), e -> {
                codePiece.append("\n");
                generateOperationCode(e, codePiece, true, "public");
            });
            codePiece.append("\n");
            generateStateMachineCode(element, codePiece);
        });
        codePiece.append("}");
    }

    void generatePropertyCode(Element element, CodePiece codePiece) {
        codePiece.append("public ");
        if (element.hasAttribute("type")) {
            Element typeElement = finder.getElementByHash(element.getAttribute("type"));
            String typePath = getPackage(typeElement);
            codePiece.append(typePath + "." + typeElement.getAttribute("name") + " ", false);
        } else {
            finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:PrimitiveType"), e -> {
                codePiece.append(primitiveType2JavaType(e.getAttribute("href")) + " ", false);
            });
        }
        codePiece.append(element.getAttribute("name") + ";\n", false);
    }

    String primitiveType2JavaType(String primitiveType) {
        String template = "pathmap://UML_LIBRARIES/UMLPrimitiveTypes.library.uml#";
        primitiveType = primitiveType.replace(template, "");
        switch (primitiveType) {
            case "Integer":
                return "java.lang.Integer";
            default:
                return "Object";
        }
    }

    void generateOperationCode(Element element, CodePiece codePiece, boolean doImplementation, String visibility) {
        codePiece.append("");
        if (visibility != null && !visibility.isEmpty()) {
            codePiece.append(visibility + " ", false);
        }
        codePiece.append("void ", false);
        codePiece.append(element.getAttribute("name") + "(", false);
        boolean[] hasPrev = { false };
        finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Parameter"), e -> {
            if (hasPrev[0]) {
                codePiece.append(", ", false);
            }
            generateParameterCode(e, codePiece);
            hasPrev[0] = true;
        });
        codePiece.append(")", false);
        if (doImplementation) {
            codePiece.append(" {\n", false);
            codePiece.block(() -> {
                codePiece.append("// DONE: DESIGNER\n");
                for (Element opaqueBehaviorElement : getOpaqueBehaviorFor(element)) {
                    generateOpaqueBehaviorCode(opaqueBehaviorElement, codePiece);
                }
                codePiece.append("// TO-DO: USER\n");
            });
            codePiece.append("}\n");
        } else {
            codePiece.append(";\n", false);
        }
    }

    // assuming the code was written in JAVA ever
    void generateOpaqueBehaviorCode(Element element, CodePiece codePiece) {
        finder.forEach(element, e -> e.getTagName().equals("body"), e -> {
            generateTextCode(e, codePiece);
        });
    }

    void generateParameterCode(Element element, CodePiece codePiece) {
        if (element.hasAttribute("type")) {
            Element typeElement = finder.getElementByHash(element.getAttribute("type"));
            String typePath = getPackage(typeElement);
            codePiece.append(typePath + "." + typeElement.getAttribute("name") + " ", false);
        } else {
            finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:PrimitiveType"), e -> {
                codePiece.append(primitiveType2JavaType(e.getAttribute("href")) + " ", false);
            });
        }
        codePiece.append(element.getAttribute("name"), false);
    }

    void generateInterfaceCode(Element element, CodePiece codePiece) {
        String elementPackage = getPackage(element);
        codePiece.append("package " + elementPackage + ";\n\n");
        codePiece.append("public interface " + element.getAttribute("name") + generateGeneralizationIfExists(element) + " {\n");
        codePiece.block(() -> {
            finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Operation"), e -> {
                generateOperationCode(e, codePiece, false, "");
            });
        });
        codePiece.append("}");
    }

    void generateDataTypeCode(Element element, CodePiece codePiece) {
        String elementPackage = getPackage(element);
        codePiece.append("package " + elementPackage + ";\n\n");
        codePiece.append("public class " + element.getAttribute("name") + generateGeneralizationIfExists(element) + " {\n");
        codePiece.block(() -> {
            finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Property"), e -> {
                generatePropertyCode(e, codePiece);
            });
        });
        codePiece.append("}");
    }

    String generateGeneralizationIfExists(Element element) {
        return generateGeneralizationIfExists(element, null, null);
    }

    // the designer has to implement interface operation when required
    // we won't do this automatically to avoid compilation errors
    String generateGeneralizationIfExists(Element element, ArrayList<String> moreExtends, ArrayList<String> moreImplements) {
        ArrayList<String> extendings = new ArrayList<>();
        ArrayList<String> implementations = new ArrayList<>();

        if (moreExtends != null)
            extendings.addAll(moreExtends);
        if (moreImplements != null)
            implementations.addAll(moreImplements);

        finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Generalization"), e -> {
            Element general = finder.getElementByHash(e.getAttribute("general"));
            if (general.hasAttribute("xmi:type")) {
                String qualifiedName = getPackage(general) + "." + general.getAttribute("name");
                if (general.getAttribute("xmi:type").equals("uml:Interface")) {
                    implementations.add(qualifiedName);
                } else {
                    extendings.add(qualifiedName);
                }
            }
        });
        StringBuilder sb = new StringBuilder();
        if (extendings.size() > 0) {
            sb.append("extends");
            sb.append(" " + extendings.get(0));
            // for now ignoring remaining elements
            // only allows one generalization
        }
        if (implementations.size() > 0) {
            if (extendings.size() > 0)
                sb.append(" ");
            sb.append("implements " + implementations.get(0));
            for (String impl : implementations.subList(1, implementations.size())) {
                sb.append(", " + impl);
            }
        }
        // remove extra space on the end because the code already has this extra space
        return sb.toString().length() > 0 ? " " + sb.toString() + "" : "";
    }

    ArrayList<Element> getOpaqueBehaviorFor(Element element) {
        String id = element.getAttribute("xmi:id");
        List<Element> filtered = finder.getElements().stream()
                .filter(e -> e.hasAttribute("specification") && e.getAttribute("specification").equals(id) &&
                    e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:OpaqueBehavior"))
                .collect(Collectors.toList());
        if (filtered.size() > 0) {
            return new ArrayList<>(filtered);
        } else {
            return new ArrayList<>();
        }
    }

    void generateSignalCode(Element element, CodePiece codePiece) {
        String elementPackage = getPackage(element);
        codePiece.append("package " + elementPackage + ";\n\n");
        codePiece.append("public class " + element.getAttribute("name") + "{\n");
        codePiece.block(() -> {
            finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Property"), e -> {
                generatePropertyCode(e, codePiece);
            });
        });
        codePiece.append("}");
    }

    void generateStateMachineCode(Element element, CodePiece codePiece) {
        codePiece.append("void initializeBehavior() {\n");
        codePiece.block(() -> {
            finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:StateMachine"), e -> {
                if (!e.hasAttribute("submachineState")) {
                    codePiece.append("stateMachines.add(create" + e.getAttribute("name") + "());\n");
                }
            });
            codePiece.append("stateMachines.stream().forEach(sm -> sm.onEntering());\n");
        });
        codePiece.append("}\n");
        finder.forEach(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:StateMachine"), e -> {
            codePiece.append("\n");
            codePiece.append("xstate.modeling.State create" + e.getAttribute("name") + "() {\n");
            codePiece.block(() -> {
                codePiece.append("xstate.modeling.build.Creator creator = new xstate.modeling.build.Creator();\n");
                codePiece.append("creator.createState(\"" + e.getAttribute("xmi:id") + "\", \"" + e.getAttribute("name") + "\");\n");
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:State"), el -> {
                    codePiece.append("creator.createState(\"" + el.getAttribute("xmi:id") + "\", \"" + el.getAttribute("name") + "\");\n");
                    if (el.hasAttribute("submachine")) {
                        codePiece.append("creator.putSubmachineOnState(\"" + el.getAttribute("xmi:id") + "\"");
                        codePiece.append(", create" +
                                finder.getElementByHash(el.getAttribute("submachine")).getAttribute("name") + "());\n", false);
                    }
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:FinalState"), el -> {
                    codePiece.append("creator.createFinalState(\"" + el.getAttribute("xmi:id") + "\");\n");
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Pseudostate"), el -> {
                    if (!el.hasAttribute("type")) {
                        String shallow = "false";
                        if (el.hasAttribute("kind") && el.getAttribute("kind").equals("shallowHistory")) {
                            shallow = "true";
                        }
                        codePiece.append("creator.createFirstState(\"" + el.getAttribute("xmi:id") + "\", " + shallow + ");\n");
                    }
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Region"), el -> {
                    codePiece.append("creator.createRegion(\"" + el.getAttribute("xmi:id") + "\");\n");
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Transition"), el -> {
                    codePiece.append("creator.createTransition(\"" + el.getAttribute("xmi:id") + "\");\n");
                }, false);
                ArrayList<String> uniqueIds = new ArrayList<>();
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Trigger"), el -> {
                    if (el.hasAttribute("event")) {
                        Element event = finder.getElementByHash(el.getAttribute("event"));
                        if (!uniqueIds.contains(event.getAttribute("xmi:id")) && event.getAttribute("xmi:type").equals("uml:SignalEvent")) {
                            Element signal = finder.getElementByHash(event.getAttribute("signal"));
                            String elementPackage = getPackage(signal);
                            codePiece.append("creator.createCodeSymbol(\"" + event.getAttribute("xmi:id") + "\", " +
                                "" + elementPackage + "." + signal.getAttribute("name") + ".class.hashCode());\n");
                            uniqueIds.add(event.getAttribute("xmi:id"));
                        }
                    }
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Transition"), el -> {
                    if (el.hasAttribute("guard")) {
                        Element guard = finder.getElementByHash(el.getAttribute("guard"));
                        finder.forEach(guard, g -> g.hasAttribute("xmi:type") && g.getAttribute("xmi:type").equals("uml:OpaqueExpression"), g -> {
                            finder.forEach(g, o -> o.getTagName().equals("body"), o -> {
                                codePiece.append("creator.recordGuard(\"" + guard.getAttribute("xmi:id") + "\", new xstate.support.Guard() {\n");
                                codePiece.block(() -> {
                                    if (!forTesting) {
                                        codePiece.append("@Override public boolean eval(xstate.support.Input input) {\n");
                                        codePiece.block(() -> {
                                            generateInputConvertionCode(el, codePiece);
                                            codePiece.append("return " + o.getTextContent() + ";\n");
                                        });
                                        codePiece.append("}\n");
                                    } else {
                                        codePiece.append("@Override public int evalInteger(xstate.support.Input input) {\n");
                                        codePiece.block(() -> {
                                            generateInputConvertionCode(el, codePiece);
                                            codePiece.append("return ");
                                            generateDistanceCodeForTesting(o, codePiece);
                                            codePiece.append(";\n", false);
                                        });
                                        codePiece.append("}\n");
                                    }
                                });
                                codePiece.append("});\n");
                            });
                        });
                    }
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Transition"), el -> {
                    finder.forEach(el, ele -> ele.getTagName().equals("effect"), ele -> {
                        if (ele.getAttribute("xmi:type").equals("uml:OpaqueBehavior")) {
                            finder.forEach(ele, elem -> elem.getTagName().equals("body"), elem -> {
                                codePiece.append("creator.recordOutput(\"" + ele.getAttribute("xmi:id") + "\", new xstate.support.Output() {\n");
                                codePiece.block(() -> {
                                    codePiece.append("@Override public void run(xstate.support.Input input) {\n");
                                    codePiece.block(() -> {
                                        generateInputConvertionCode(el, codePiece);
                                        generateTextCode(elem, codePiece);
                                    });
                                    codePiece.append("}\n");
                                });
                                codePiece.append("});\n");
                            });
                        }
                    });
                }, false);
                finder.forEach(e, el -> el.getTagName().equals("entry") || el.getTagName().equals("exit"), el -> {
                    codePiece.append("creator.recordOutput(\"" + el.getAttribute("xmi:id") + "\", new xstate.support.Output() {\n");
                    codePiece.block(() -> {
                        codePiece.append("@Override public void run(xstate.support.Input input) {\n");
                        codePiece.block(() -> {
                            if (el.getAttribute("xmi:type").equals("uml:OpaqueBehavior")) {
                                finder.forEach(el, ele -> ele.getTagName().equals("body"), ele -> {
                                    generateTextCode(ele, codePiece);
                                });
                            }
                        });
                        codePiece.append("}\n");
                    });
                    codePiece.append("});\n");
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:State"), el -> {
                    codePiece.append("creator.putStateOnRegion(\"" + ((Element) el.getParentNode()).getAttribute("xmi:id") + "\", " +
                        "\"" + el.getAttribute("xmi:id") + "\");\n");
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:FinalState"), el -> {
                    codePiece.append("creator.putFinalStateOnRegion(\"" + ((Element) el.getParentNode()).getAttribute("xmi:id") + "\", " +
                            "\"" + el.getAttribute("xmi:id") + "\");\n");
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Region"), el -> {
                    codePiece.append("creator.putSubRegionOnState(\"" + ((Element) el.getParentNode()).getAttribute("xmi:id") + "\", " +
                        "\"" + el.getAttribute("xmi:id") + "\");\n");
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Pseudostate"), el -> {
                    if (!el.hasAttribute("type")) {
                        codePiece.append("creator.putFirstStateOnRegion(\"" + ((Element) el.getParentNode()).getAttribute("xmi:id") + "\", " +
                            "\"" + el.getAttribute("xmi:id") + "\");\n");
                    }
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Transition"), el -> {
                    codePiece.append("creator.putTransitionBetweenNodes(\"" + el.getAttribute("xmi:id") + "\", " +
                        "\"" + el.getAttribute("source") + "\", \"" + el.getAttribute("target") + "\");\n");
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Transition"), el -> {
                    finder.forEach(el, ele -> ele.hasAttribute("xmi:type") & ele.getAttribute("xmi:type").equals("uml:Trigger"), ele -> {
                        codePiece.append("creator.putSymbolOnTransition(\"" + el.getAttribute("xmi:id") + "\", \"" +
                            ele.getAttribute("event") + "\");\n");
                    });
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Transition"), el -> {
                    if (el.hasAttribute("guard")) {
                        codePiece.append("creator.putGuardOnTransition(\"" + el.getAttribute("xmi:id") + "\", \"" +
                            el.getAttribute("guard") + "\");\n");
                    }
                }, false);
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:Transition"), el -> {
                    finder.forEach(el, ele -> ele.getTagName().equals("effect"), ele -> {
                        codePiece.append("creator.putOutputOnTransition(\"" + el.getAttribute("xmi:id") + "\", \"" +
                            ele.getAttribute("xmi:id") + "\");\n");
                    });
                });
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:State"), el -> {
                    finder.forEach(el, ele -> ele.getTagName().equals("entry"), ele -> {
                        codePiece.append("creator.putOutputOnStateForEntering(\"" + el.getAttribute("xmi:id") + "\", \"" +
                            ele.getAttribute("xmi:id") + "\");\n");
                    });
                });
                finder.forEach(e, el -> el.hasAttribute("xmi:type") && el.getAttribute("xmi:type").equals("uml:State"), el -> {
                    finder.forEach(el, ele -> ele.getTagName().equals("exit"), ele -> {
                        codePiece.append("creator.putOutputOnStateForExiting(\"" + el.getAttribute("xmi:id") + "\", \"" +
                                ele.getAttribute("xmi:id") + "\");\n");
                    });
                });
                // to filter by classifier too
                codePiece.append("creator.setClassifierId(classifierId);\n");
                codePiece.append("return (xstate.modeling.State) creator.getNode(\"" + e.getAttribute("xmi:id") + "\");\n");
            });
            codePiece.append("}\n");
        });
        codePiece.append("\n");
        codePiece.append("@Override public void onReceive(xstate.support.Input input) {\n");
        codePiece.block(() -> {
            codePiece.append("stateMachines.stream().forEach(sm -> sm.onInput(input));\n");
        });
        codePiece.append("}\n");
    }

    void generateInputConvertionCode(Element element, CodePiece codePiece) {
        finder.forEach(element, v -> v.hasAttribute("xmi:type") && v.getAttribute("xmi:type").equals("uml:Trigger"), v -> {
            if (v.hasAttribute("event")) {
                Element event = finder.getElementByHash(v.getAttribute("event"));
                if (event.getAttribute("xmi:type").equals("uml:SignalEvent")) {
                    Element signal = finder.getElementByHash(event.getAttribute("signal"));
                    String signalPackage = getPackage(signal);
                    codePiece.append(signalPackage + "." + signal.getAttribute("name") +
                            " event = xstate.support.Input.createFrom(input, " + signalPackage + "." + signal.getAttribute("name") + ".class);\n");
                }
            }
        });
    }

    void generateDistanceCodeForTesting(Element element, CodePiece codePiece) {
        String constraint = element.getTextContent();
        String newExpression = new DistanceBranchParser().parse(constraint);
        codePiece.append(newExpression, false);
    }

    void generateTextCode(Element element, CodePiece codePiece) {
        String code = element.getTextContent();
        code = code.replace("\r", "");
        for (String codeLine : code.split(";")) {
            String[] newLines = codeLine.split("\n");
            for (int i = 0; i < newLines.length; i++) {
                if (i < newLines.length - 1) {
                    codePiece.append(newLines[i] + "\n");
                } else {
                    codePiece.append(newLines[i] + ";\n");
                }
            }
        }
    }

    String getPackage(Element element) {
        ArrayList<Element> packagePath = finder.getPathFrom(element, e -> e.hasAttribute("xmi:type") && e.getAttribute("xmi:type").equals("uml:Package"));
        ArrayList<String> sPackagePath = new ArrayList<>(packagePath.stream().map(e -> e.getAttribute("name")).collect(Collectors.toList()));
        return String.join(".", sPackagePath);
    }

    public ArrayList<CodePiece> getCodePieces() {
        return codePieces;
    }

    public class CodePiece {
        String name;
        StringBuilder sb = new StringBuilder();
        String tabSpace = "    ";
        String indentation = "";

        public void setName(String name) {
            this.name = name;
        }

        public void append(Object obj) {
            append(obj, true);
        }

        public void append(Object obj, boolean indent) {
            if (indent)
                sb.append(indentation);
            sb.append(obj);
        }

        public void block(Runnable runnable) {
            incrIndentation();
            runnable.run();
            decrIndentation();
        }

        public void incrIndentation() {
            indentation = indentation + tabSpace;
        }

        public void decrIndentation() {
            if (indentation.length() - tabSpace.length() >= 0) {
                indentation = indentation.substring(0, indentation.length() - tabSpace.length());
            } else {
                indentation = "";
            }
        }

        @Override
        public String toString() {
            return sb.toString();
        }

        public String getName() {
            return name;
        }
    }
}
