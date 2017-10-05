package geo.main;

import geo.algorithm.BinaryInteger;
import geo.algorithm.Geo;
import geo.algorithm.GeoVar;
import geo.problem.Booth;

public class Application {
    public static void main(String[] args) {
        System.out.println("Hello World!");
        Geo geo = new GeoVar(
                1.0,
                50000,
                new Booth.ObjectiveOne(),
                Booth.searchDomain);
        geo.run();
        System.out.println("The End!");
        double x = Booth.getX(geo.getBestSequence());
        double y = Booth.getY(geo.getBestSequence());
        System.out.println("x=" + x + ", y=" + y);
        System.out.println("Best iteration is " + geo.getBestIteration());
    }
}