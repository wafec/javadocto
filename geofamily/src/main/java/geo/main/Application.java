package geo.main;

import geo.algorithm.BinaryInteger;
import geo.algorithm.Geo;
import geo.algorithm.GeoVar;
import geo.problem.Booth;

public class Application {
    public static void main(String[] args) {
        System.out.println("Hello World!");
        Geo geo = new Geo(
                1.0,
                50000,
                new Booth.ObjectiveOne(),
                Booth.searchDomain);
        geo.run();
        System.out.println("The End!");
        int x = (geo.getBestSequence().getProjectVariables()[0].getValue() - 10);
        int y = (geo.getBestSequence().getProjectVariables()[1].getValue() - 10);
        System.out.println("x=" + x + ", y=" + y);
        System.out.println("Best iteration is " + geo.getBestIteration());
    }
}