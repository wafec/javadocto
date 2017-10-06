package geo.main;

import geo.algorithm.*;
import geo.problem.Booth;
import geo.problem.Kursawe;

import java.util.Collections;
import java.util.List;

public class Application {
    public static void main(String[] args) {
        System.out.println("Hello World!");
        mGeoTest();
        System.out.println("The End!");
    }

    private static void geoTest() {
        Geo geo = new GeoVar(
                1.0,
                50000,
                new Booth.ObjectiveOne(),
                Booth.searchDomain);
        geo.run();
        double x = Booth.getX(geo.getBestSequence());
        double y = Booth.getY(geo.getBestSequence());
        System.out.println("x=" + x + ", y=" + y);
        System.out.println("Best iteration is " + geo.getBestIteration());
    }

    private static void mGeoTest() {
        Mgeo mGeo = new Mgeo(
                1.5,
                100000,
                10,
                new Objective[] { new Kursawe.ObjectiveOne(), new Kursawe.ObjectiveTwo()},
                Kursawe.searchDomain
        );
        mGeo.run();
        System.out.println("Pareto Frontier Size = " + mGeo.getParetoFrontier().getElements().size());
        ParetoFrontier paretoFrontier = mGeo.getParetoFrontier();
        List<ParetoFrontier.Element> elements = paretoFrontier.getElements();
        Collections.sort(elements, (o1, o2) -> {
            return Double.compare(o1.getObjectivesRates()[0], o2.getObjectivesRates()[0]);
        });
        for (ParetoFrontier.Element element : elements) {
            System.out.printf("%11.7f %11.7f %6d %n", element.getObjectivesRates()[0], element.getObjectivesRates()[1], element.getIterationIndex());
        }
    }
}